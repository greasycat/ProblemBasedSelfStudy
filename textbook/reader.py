import os
from pathlib import Path
import io
import tempfile
import json
from typing import Optional, List

from PIL import Image
import pymupdf

from pydantic import BaseModel
import structlog

from textbook.database import TextBookDatabase, BookInfo, ChapterInfo
from textbook.model import LLM
from textbook.mineru import MinerURequest
from textbook.utils import detect_toc

MAX_PAGE_FOR_TOC_DETECTION = 15 # Number of pages to read for TOC detection
MAX_PAGE_FOR_ALIGNMENT_CHECK = 25 # Number of pages to read for alignment check in worst case, this is longer than the TOC detection because we may need to check both TOC and prefaces if TOC end is not set
MIN_PAGE_CONTENT_LENGTH = 20 # Minimum length of page content to be considered valid

def cover_prompt(cover: str) -> str:
    return f"""
    Extract 
    1. book title (lower case all letters)
    2. author information (lower case all letters)
    3. keywords to best describe the book content, do not include edition or publisher or license information in keywords
    
    from the following text of the book cover:
    {cover}
    """

def toc_prompt(toc: str) -> str:

    # replace line breaks with <BREAK>
    toc = toc.replace("\n", "<LINE BREAK>")

    return f"""
    Extract 
    1. The table of contents from the following text (lower case all letters)
    2. Treat bibliography and indexes as two separate chapters: 
    3. If preface, about page, acknowledgements page and any other pages that are not relevant to the content of the book, do not include them in the table of contents
    
    from the following text:
    {toc}
    """

def page_summary_prompt(page: str, related_chapters: List[str], related_sections: List[str]) -> str:
    return f"""
    Extract the summary of the following page text with rules:
    - use bullet points to summarize the page content, identify any key definitions or remarks, assume all the points will be used for an advance exam
    - if it contain more than one exercises, mark this page as containing exercise,
    - do not summarize the exercises, just mark this page as containing exercise
    - if it the page contain more than one chapter or section, summarize the chapter or section separately
    - all title should be not contain any symbols
    - all title should be in lower case

    Page: 
     {page}
    """

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

class PageSummarySchema(BaseModel):
    title: str
    summary: str

class PageSchema(BaseModel):
    page_summary: List[PageSummarySchema]
    has_exercises: bool

    def full_summary(self) -> str:
        return "\n".join([f"{summary.title}: {summary.summary}" for summary in self.page_summary])


class LazyTextbookReader:
    
    def __init__(self, pdf_path: Path, llm: LLM, database: TextBookDatabase, force_text_only_extraction: bool = False):

        self.logger = structlog.get_logger(__name__)

        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        self.pdf_path = pdf_path
        self.pdf_name = self.pdf_path.stem

        self.llm = llm

        self.pdf_document: Optional[pymupdf.Document] = None
        
        self.database: TextBookDatabase = database

        self.force_text_only_extraction = force_text_only_extraction

        # Current book ID
        self.book_info: Optional[BookInfo] = None

    def __enter__(self):
        if not os.path.exists(self.pdf_path):
            raise FileNotFoundError(f"PDF file not found: {self.pdf_path}")
        else:
            self.logger.info(f"PDF file found: {self.pdf_path}")

        self.pdf_document = pymupdf.open(self.pdf_path)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.pdf_document:
            self.pdf_document.close()

    # ------------------------------------------------------------
    # PDF related functions
    # ------------------------------------------------------------
    
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
    
    def get_page_content(self, page_number: int, apply_alignment_offset: bool = False) -> str:
        if apply_alignment_offset and self.book_info is not None and self.book_info.book_alignment_offset is not None:
            page_number = page_number + self.book_info.book_alignment_offset

        extracted_text = self.get_page_as_text(page_number).strip()

        if len(extracted_text) < MIN_PAGE_CONTENT_LENGTH and not self.force_text_only_extraction:
            self.logger.warning(f"Page {page_number} content is too short, try to extract from image")
            return self.get_page_as_text_from_image(page_number)
        else:
            return extracted_text
        
    # ------------------------------------------------------------
    # Book related functions
    # ------------------------------------------------------------

    def check_if_book_exists_and_load(self) -> bool:
        book = self.database.get_book_by_file_name(self.pdf_name)
        if book is not None:
            self.book_info = book
            return True
        self.logger.warning(f"Book {self.pdf_name} not found in database")
        return False
    
    def update_book_info(self):
        self.logger.debug(f"Updating book info for {self.pdf_name}")
        cover = self.get_page_content(0) # Get the first page of the book
        book_basic_info = self.llm.prompt_with_schema(cover_prompt(cover), schema=BookSchema)
        # deserialize the response to a BookBasicInfo object
        book_info = self.database.create_book(book_basic_info.book_name, book_basic_info.book_author, book_basic_info.book_keywords, self.pdf_name, self.get_total_pages())
        self.book_info = book_info

    # ------------------------------------------------------------
    # TOC related functions
    # ------------------------------------------------------------

    def check_if_toc_exists(self) -> bool:
        if self.book_info is None:
            return False
        with self.database.new_session() as session:
            toc = session.query(ChapterInfo).filter(ChapterInfo.book_id == self.book_info.book_id).all()
            return len(toc) > 0
        
    def update_toc(self, caching: bool = True, overwrite: bool = False):
        if self.book_info is None:
            self.logger.error("Book basic information not extracted, please extract it first")
            raise ValueError("Book basic information not extracted, please extract it first")

        if not overwrite and self.check_if_toc_exists():
            self.logger.info(f"TOC already exists for book {self.book_info.book_id}, skipping overwrite")
            return

        # TODO: Remove caching
        # if caching and os.path.exists("toc.json"):
        #     with open("toc.json", "r") as f:
        #         toc = json.load(f)
        #         self.save_toc(toc)
        #         return toc

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

        self.database.update_book_toc_end_page(self.book_info.book_id, toc_end_page)
        
        try:
            self.logger.info(f"Sending TOC to LLM for book {self.book_info.book_id}, {toc[:100]}... ")
            toc = self.llm.prompt_with_schema(toc_prompt(toc), schema=TocSchema)
            self.logger.info(f"TOC extracted for book {self.book_info.book_id}")
        except Exception as e:
            self.logger.error(f"Failed to extract TOC for book {self.book_info.book_id}: {e}")
            raise ValueError(f"Failed to extract TOC for book {self.book_info.book_id}: {e}")

        # if caching:
        #     with open("toc.json", "w") as f:
        #         f.write(toc.model_dump_json())

        self.save_toc(toc.model_dump())
    
    def delete_toc(self):
        if self.book_info is None or self.book_info.book_id is None:
            raise ValueError("Book basic information not extracted, please extract it first")
        
        self.logger.info(f"Deleting TOC for book {self.book_info.book_id}")
        self.database.delete_toc_by_book_id(self.book_info.book_id)
        self.logger.info(f"TOC deleted for book {self.book_info.book_id}")
    
        if self.check_if_toc_exists():
            self.logger.error(f"TOC still exists for book {self.book_info.book_id}, skipping deletion")
            raise ValueError(f"TOC still exists for book {self.book_info.book_id}, skipping deletion")
    

    
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
        
        # delete the existing TOC
        self.logger.info(f"Deleting existing TOC for book {self.book_info.book_id} before saving new TOC")
        self.delete_toc()
        
        for chapter, start_page_number, end_page_number in self.generate_block_with_range(toc["chapters"], self.get_total_pages()-1):
            chapter_id = self.database.try_create_chapter_info(
                self.book_info.book_id,
                title=chapter["title"],
                index_string=chapter["index_string"],
                start_page=start_page_number,
                end_page=end_page_number,
            )

            if chapter_id is None:
                continue
                
            for section, start_page_number, end_page_number in self.generate_block_with_range(chapter["sections"], end_page_number+1): # +1 because the end page number from the parent chapter is inclusive
                section_id = self.database.try_create_section_info(
                    self.book_info.book_id,
                    chapter_id,
                    title=section["title"],
                    index_string=section["index_string"],
                    start_page=start_page_number,
                    end_page=end_page_number,
                )

                if section_id is None:
                    continue

    # ------------------------------------------------------------
    # Alignment related functions
    # ------------------------------------------------------------

    def update_alignment_offset(self, page_number: int):
        if self.book_info is None or self.book_info.book_id is None:
            raise ValueError("Book basic information not extracted, please extract it first")
        
        self.database.update_book_alignment_offset(self.book_info.book_id, page_number)
        self.book_info.book_alignment_offset = page_number
    

    def check_alignment_offset(self) -> List[str]:
        if self.book_info is None or self.book_info.book_id is None:
            return []

        chapters = self.database.get_chapters_by_book_id(self.book_info.book_id)
        if len(chapters) < 2:
            print("Not enough chapters to check alignment, skipping alignment check")
            return []

        results = []

        offset = self.database.get_book_alignment_offset(self.book_info.book_id, default_value=0)
        chapter_2_page_number = chapters[1].start_page_number
        page_text = self.get_page_content(chapter_2_page_number + offset)

        results.append(page_text)

        sections = self.database.get_sections_by_book_id(self.book_info.book_id)
        if len(sections) < 1:
            return results

        section_1_page_number = sections[0].start_page_number
        section_1_text = self.get_page_content(section_1_page_number + offset)
        results.append(section_1_text)

        return results
    
    # ------------------------------------------------------------
    # Page related functions
    # ------------------------------------------------------------

    def create_or_update_page_info(self, page_number: int):
        if self.book_info is None or self.book_info.book_id is None:
            raise ValueError("Book basic information not extracted, please extract it first")

        # get the related chapters and sections
        related_chapters = [chapter.title for chapter in self.database.get_chapters_by_book_id_and_page_range(self.book_info.book_id, page_number, page_number)]
        related_sections = [section.title for section in self.database.get_sections_by_book_id_and_page_range(self.book_info.book_id, page_number, page_number)]
        
        page_text = self.get_page_content(page_number)
        page_summary = self.llm.prompt_with_schema(page_summary_prompt(page_text, related_chapters, related_sections), schema=PageSchema)

        page_id = self.database.try_create_page_info(self.book_info.book_id, page_number, page_summary.full_summary())

        return page_id


