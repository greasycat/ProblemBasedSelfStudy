import os
from pathlib import Path
import io
import tempfile
import json
import readchar
from typing import Optional, List

from PIL import Image
import pymupdf

from pydantic import BaseModel

from textbook.context import TextBookContext, BookInfo, ChapterInfo
from textbook.model import LLM
from textbook.mineru import MinerURequest
from textbook.utils import detect_toc

MAX_PAGE_FOR_TOC_DETECTION = 15 # Number of pages to read for TOC detection
MAX_PAGE_FOR_ALIGNMENT_CHECK = 25 # Number of pages to read for alignment check in worst case, this is longer than the TOC detection because we may need to check both TOC and prefaces if TOC end is not set

# Pydantic model for TOC
class SectionSchema(BaseModel):
    index_string: str
    title: str
    page_number: int

class ChapterSchema(BaseModel):
    index_string: str
    title: str
    page_number: int
    sections: List[SectionSchema]

class TocSchema(BaseModel):
    chapters: List[ChapterSchema]

class BookSchema(BaseModel):
    book_name: str
    book_author: str
    book_keywords: str

class PageSchema(BaseModel):
    page_summary: str
    does_contain_exercise: bool



class LazyTextbookReader:
    
    def __init__(self, pdf_path: Path, llm: LLM, context: TextBookContext, force_text_only_extraction: bool = False):
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        self.pdf_path = pdf_path
        self.pdf_name = self.pdf_path.stem

        self.llm = llm

        self.pdf_document: Optional[pymupdf.Document] = None
        
        self.context: TextBookContext = context

        self.force_text_only_extraction = force_text_only_extraction

        # Current book ID
        self.book_info: Optional[BookInfo] = None

    def __enter__(self):
        self.pdf_document = pymupdf.open(self.pdf_path)
        self.check_if_book_exists_and_load()
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
        book = self.context.get_book_by_file_name(self.pdf_name)
        if book is not None:
            self.book_info = book
            return True
        return False
    
    def update_book_info(self, overwrite: bool = False) -> None:
        if not overwrite and self.book_info is not None:
            print(f"Book {self.pdf_name} already exists, skipping extraction, if you want to overwrite, set overwrite to True")
            return

        cover = self.get_page_content(0) # Get the first page of the book
        response = self.llm.text_model.prompt(f"Extract the book information from the following text: {cover}, use keywords to best summarize the book, do not include edition information in keywords", schema=BookSchema)
        # deserialize the response to a BookBasicInfo object
        book_basic_info = BookSchema.model_validate_json(response.text())
        book_info = self.context.create_book(book_basic_info.book_name, book_basic_info.book_author, book_basic_info.book_keywords, self.pdf_name)
        self.book_info = book_info

    def check_if_toc_exists(self) -> bool:
        if self.book_info is None:
            return False
        with self.context.new_session() as session:
            toc = session.query(ChapterInfo).filter(ChapterInfo.book_id == self.book_info.book_id).all()
            return len(toc) > 0
        
    def update_toc(self, caching: bool = True, overwrite: bool = False):
        if self.book_info is None:
            raise ValueError("Book basic information not extracted, please extract it first")

        # TODO: Remove caching
        if caching and os.path.exists("toc.json"):
            with open("toc.json", "r") as f:
                toc = json.load(f)
                self.save_toc(toc)
                return toc

        toc = ""
        toc_start = False
        number_of_toc_pages = 0
        toc_end_page = 0
        for page_num in range(0, MAX_PAGE_FOR_TOC_DETECTION):
            page_text = self.get_page_content(page_num)
            is_toc = detect_toc(page_text)
            if not toc_start and is_toc:
                toc_start = True
            if toc_start:
                toc += page_text
                number_of_toc_pages += 1
            if toc_start and not is_toc:
                toc_end_page = page_num
                break

        self.context.update_book_toc_end_page(self.book_info.book_id, toc_end_page)
        
        toc = self.llm.text_model.prompt(f"Extract the table of contents from the following text, treat bibliography and indexes as two separate chapters: {toc}", schema=TocSchema)

        if caching:
            with open("toc.json", "w") as f:
                f.write(toc.text())

        self.save_toc(json.loads(toc.text()))
    
    @staticmethod
    def generate_block_with_range(block_list, end_page_number: int):
        # append a end placeholder chapter to the target list
        block_list.append({
            "title": "<END>",
            "page_number": end_page_number,
        })

        for i in range(len(block_list)-1):
            block = block_list[i]
            next_block = block_list[i+1]

            yield block, block['page_number'], next_block['page_number']-1


    def save_toc(self, toc: dict):
        if self.book_info is None or self.book_info.book_id is None:
            raise ValueError("Book basic information not extracted, please extract it first")

        for chapter, start_page_number, end_page_number in self.generate_block_with_range(toc["chapters"], self.get_total_pages()-1):
            chapter_id = self.context.get_or_create_chapter(
                self.book_info.book_id,
                title=chapter["title"],
                index_string=chapter["index_string"],
                start_page=start_page_number,
                end_page=end_page_number,
            )

            if chapter_id is None:
                continue
                
            for section, start_page_number, end_page_number in self.generate_block_with_range(chapter["sections"], end_page_number+1): # +1 because the end page number from the parent chapter is inclusive
                section_id = self.context.get_or_create_section(
                    self.book_info.book_id,
                    chapter_id,
                    title=section["title"],
                    index_string=section["index_string"],
                    start_page=start_page_number,
                    end_page=end_page_number,
                )

                if section_id is None:
                    continue

    def update_alignment_offset(self, page_number: int):
        if self.book_info is None or self.book_info.book_id is None:
            raise ValueError("Book basic information not extracted, please extract it first")
        
        self.context.update_book_alignment_offset(self.book_info.book_id, page_number)
        self.book_info.book_alignment_offset = page_number
    
    def interactive_alignment_offset(self):
        if self.book_info is None or self.book_info.book_id is None:
            raise ValueError("Book basic information not extracted, please extract it first")

        chapters = self.context.get_chapters_by_book_id(self.book_info.book_id)
        if len(chapters) < 0:
            raise ValueError("No chapters found, please update the TOC first")

        first_chapter_page_number = chapters[0].start_page_number

        toc_end_page = self.context.get_book_toc_end_page(self.book_info.book_id, default_value=0)
        page_number = toc_end_page+1
        while page_number < self.get_total_pages():
            page_text = self.get_page_content(page_number)
            print("="*40)
            print(page_text)
            print("="*40)
            print("Is this the first chapter? (y/j/k): ")
            key = readchar.readkey()
            if key == 'y':
                print("Press enter to confirm, other key to cancel")
                offset = page_number - first_chapter_page_number
                print(f"Alignment offset: {offset}")
                self.update_alignment_offset(offset)
                break
            elif key == 'j':
                if page_number == self.get_total_pages()-1:
                    print("You are at the last page, cannot go forward")
                    continue
                page_number += 1
            elif key == 'k':
                if page_number == 1:
                    print("You are at the first page, cannot go back")
                    continue
                page_number -= 1
        
        # get chapter 2 page number
        if len(chapters) < 2:
            print("Not enough chapters to check alignment, skipping alignment check")
            return

    def check_alignment_offset(self) -> List[str]:
        if self.book_info is None or self.book_info.book_id is None:
            return []

        chapters = self.context.get_chapters_by_book_id(self.book_info.book_id)
        if len(chapters) < 2:
            print("Not enough chapters to check alignment, skipping alignment check")
            return []

        results = []

        offset = self.context.get_book_alignment_offset(self.book_info.book_id, default_value=0)
        chapter_2_page_number = chapters[1].start_page_number
        page_text = self.get_page_content(chapter_2_page_number + offset)

        results.append(page_text)

        sections = self.context.get_sections_by_book_id(self.book_info.book_id)
        if len(sections) < 1:
            return results

        section_1_page_number = sections[0].start_page_number
        section_1_text = self.get_page_content(section_1_page_number + offset)
        results.append(section_1_text)

        return results