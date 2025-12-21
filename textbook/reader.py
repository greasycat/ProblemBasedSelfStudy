import os
from pathlib import Path
import io
import tempfile
import json

from typing import Optional, List

from PIL import Image
import pymupdf

from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

from textbook.context import TextBookContext, BookInfo, ChapterInfo, SectionInfo, PageInfo, ExerciseInfo, ExerciseDetails
from textbook.model import LLM
from textbook.mineru import MinerURequest
from textbook.utils.toc_detection import detect_toc

MAX_PAGE_FOR_TOC_DETECTION = 15 # Number of pages to read for TOC detection

# Pydantic model for TOC
class TocSection(BaseModel):
    index_string: str
    title: str
    page_number: int

class TocChapter(BaseModel):
    index_string: str
    title: str
    page_number: int
    sections: List[TocSection]

class Toc(BaseModel):
    chapters: List[TocChapter]

class BookBasicInfo(BaseModel):
    book_name: str
    book_author: str
    book_keywords: str


class LazyTextbookReader:
    
    def __init__(self, pdf_path: str, llm: LLM, context: TextBookContext, force_text_only_extraction: bool = False):
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        self.pdf_path = Path(pdf_path)
        self.pdf_name = self.pdf_path.stem

        self.llm = llm

        self.pdf_document: Optional[pymupdf.Document] = None
        
        self.context: TextBookContext = context

        self.force_text_only_extraction = force_text_only_extraction

        # Current book ID
        self.book_info: Optional[BookInfo] = None

    def __enter__(self):
        self.pdf_document = pymupdf.open(self.pdf_path)
        self.book_info = self.extract_book_info()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.pdf_document:
            self.pdf_document.close()
    
    def get_total_pages(self) -> int:
        if not self.pdf_document:
            raise RuntimeError("PDF document not opened. Use context manager.")
        return max(len(self.pdf_document), 1)
    
    def get_page_as_text(self, page_number: int) -> str:
        if not self.pdf_document:
            raise RuntimeError("PDF document not opened. Use context manager.")
        
        if page_number < 0 or page_number >= len(self.pdf_document):
            raise ValueError(f"Page number {page_number} out of range [0, {len(self.pdf_document)})")
        
        page = self.pdf_document[page_number]
        text = page.get_text()
        if isinstance(text, str):
            return text
        else:
            raise ValueError(f"Unsupported text type: {type(text)}")
    
    def get_page_as_image(self, page_number: int, dpi: int = 150) -> Image.Image:
        if not self.pdf_document:
            raise RuntimeError("PDF document not opened. Use context manager.")
        
        if page_number < 0 or page_number >= len(self.pdf_document):
            raise ValueError(f"Page number {page_number} out of range [0, {len(self.pdf_document)})")
        
        page = self.pdf_document[page_number]
        mat = pymupdf.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        return img
    
    def get_page_as_text_from_image(self, page_number: int) -> str:
        if not self.pdf_document:
            raise RuntimeError("PDF document not opened. Use context manager.")
        
        img = self.get_page_as_image(page_number)
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        img.save(tmp_path, 'PNG')
        
        try:
            request = MinerURequest(files=[tmp_path])
            request.set_return_md(True)
            request.set_start_page_id(0)
            request.set_end_page_id(0)
            
            results = request.request()
            
            if results:
                for file_result in results.values():
                    if 'md_content' in file_result:
                        return file_result['md_content']
                for file_result in results.values():
                    if isinstance(file_result, dict):
                        for key in ['content', 'text', 'markdown', 'md_content']:
                            if key in file_result:
                                return str(file_result[key])
            
            return ""
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def get_page_content(self, page_number: int) -> str:
        if not self.force_text_only_extraction:
            return self.get_page_as_text_from_image(page_number)
        else:
            return self.get_page_as_text(page_number)
        
    def check_if_book_exists_and_load(self) -> bool:
        with self.context.new_session() as session:
            book = session.query(BookInfo).filter(BookInfo.book_file_name == self.pdf_name).first()
            if book is not None:
                self.book_info = book
                return True
            return False
    
    def extract_book_info(self, overwrite: bool = False) -> Optional[BookInfo]:
        if self.check_if_book_exists_and_load() and not overwrite:
            print(f"Book {self.pdf_name} already exists, skipping extraction, if you want to overwrite, set overwrite to True")
            return
        
        cover = self.get_page_content(0) # Get the first page of the book
        response = self.llm.text_model.prompt(f"Extract the book information from the following text: {cover}", schema=BookBasicInfo)
        # deserialize the response to a BookBasicInfo object
        book_basic_info = BookBasicInfo.model_validate_json(response.text())
        with self.context.new_session() as session:
            book_info = BookInfo(
                book_name=book_basic_info.book_name,
                book_author=book_basic_info.book_author,
                book_keywords=book_basic_info.book_keywords,
                book_file_name=self.pdf_name,
            )
            session.add(book_info)
            session.commit()
            session.refresh(book_info)
        return book_info

    def check_if_toc_exists(self) -> bool:
        if self.book_info is None:
            return False
        with self.context.new_session() as session:
            toc = session.query(ChapterInfo).filter(ChapterInfo.book_id == self.book_info.book_id).all()
            return len(toc) > 0
        
    def extract_toc(self, caching: bool = True, overwrite: bool = False):
        if self.book_info is None:
            raise ValueError("Book basic information not extracted, please extract it first")

        if caching and os.path.exists("toc.json"):
            with open("toc.json", "r") as f:
                toc = json.load(f)
                self.save_toc(toc)
                return toc

        toc = ""
        toc_start = False
        number_of_toc_pages = 0
        for page_num in range(0, MAX_PAGE_FOR_TOC_DETECTION):
            page_text = self.get_page_content(page_num)
            is_toc = detect_toc(page_text)
            if not toc_start and is_toc:
                toc_start = True
            if toc_start:
                toc += page_text
                number_of_toc_pages += 1
            if toc_start and not is_toc:
                break

        
        toc = self.llm.text_model.prompt(f"Extract the table of contents from the following text, treat bibliography and indexes as two separate chapters: {toc}", schema=Toc)

        if caching:
            with open("toc.json", "w") as f:
                f.write(toc.text())

        self.save_toc(json.loads(toc.text()))
    
    def save_toc(self, toc: dict):
        if self.book_info is None:
            raise ValueError("Book basic information not extracted, please extract it first")

        toc['chapters'].append({
            "title": "END OF BOOK",
            "page_number": self.get_total_pages()-1,
        })

        for i in range(0, len(toc['chapters'])-1):
            chapter = toc['chapters'][i]
            next_chapter = toc['chapters'][i+1]
            end_page_number = next_chapter['page_number']-1

            chapter_info = ChapterInfo(
                title=chapter['title'],
                book_index_string=chapter['index_string'],
                start_page_number=chapter['page_number'],
                end_page_number=end_page_number,
                book_id=self.book_info.book_id
            )

            self.save_section(chapter['sections'], chapter_info.chapter_id, end_page_number)

            try:
                self.context.session.add(chapter_info)
                self.context.session.commit()
            except IntegrityError:
                print(f"Chapter {chapter['title']} already exists, skipping")
                self.context.session.rollback()
                continue
            except Exception as e:
                print(f"Error adding chapter {chapter['title']}: {e}")
                self.context.session.rollback()
                continue

    def save_section(self, sections: list[dict], chapter_id: int, end_page_number: int):
        if self.book_info is None:
            raise ValueError("Book basic information not extracted, please extract it first")
        
        sections.append({
            "title": "END OF CHAPTER",
            "page_number": end_page_number,
        })
        

        for i in range(0, len(sections)-1):
            section = sections[i]
            next_section = sections[i+1]
            end_page_number = next_section['page_number']-1

            section_info = SectionInfo(
                title=section['title'],
                start_page_number=section['page_number'],
                end_page_number=end_page_number,
                book_index_string=section['index_string'],
                book_id=self.book_info.book_id,
                chapter_id=chapter_id
            )

            try:
                self.context.session.add(section_info)
                self.context.session.commit()
            except IntegrityError:
                print(f"Section {section['title']} already exists, skipping")
                self.context.session.rollback()
                continue
            except Exception as e:
                print(f"Error adding section {section['title']}: {e}")
                self.context.session.rollback()
                continue