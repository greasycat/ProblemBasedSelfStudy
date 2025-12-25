from pydantic import BaseModel, Field
from typing import Optional, List

class UploadBookResponse(BaseModel):
    book_id: int
    message: str


class DeleteBookResponse(BaseModel):
    book_id: int
    message: str
    deleted: bool

class BookIdRequest(BaseModel):
    book_id: int = Field(..., description="ID of the book")


class PageNumberRequest(BaseModel):
    book_id: int = Field(..., description="ID of the book")
    page_number: int = Field(..., ge=0, description="Page number (0-indexed)")


class PageImageRequest(BaseModel):
    book_id: int = Field(..., description="ID of the book")
    page_number: int = Field(..., ge=0, description="Page number (0-indexed)")
    dpi: int = Field(default=150, ge=72, le=300, description="DPI for image rendering")


class UpdateBookInfoRequest(BaseModel):
    book_id: int = Field(..., description="ID of the book")
    overwrite: bool = Field(default=False, description="Whether to overwrite existing book info")


class UpdateTocRequest(BaseModel):
    book_id: int = Field(..., description="ID of the book")
    caching: bool = Field(default=True, description="Whether to cache TOC results")
    overwrite: bool = Field(default=False, description="Whether to overwrite existing TOC")


class UpdateAlignmentOffsetRequest(BaseModel):
    book_id: int = Field(..., description="ID of the book")
    page_number: int = Field(..., ge=0, description="Page number for alignment offset")


class UpdateBookFieldsRequest(BaseModel):
    book_id: int = Field(..., description="ID of the book")
    book_name: Optional[str] = Field(default=None, description="Name/title of the book")
    book_author: Optional[str] = Field(default=None, description="Author of the book")
    book_keywords: Optional[str] = Field(default=None, description="Keywords associated with the book")
    alignment_offset: Optional[int] = Field(default=None, description="Alignment offset for page number correction")


class CheckAlignmentOffsetRequest(BaseModel):
    book_id: int = Field(..., description="ID of the book")


class TotalPagesResponse(BaseModel):
    book_id: int
    total_pages: int


class PageTextResponse(BaseModel):
    book_id: int
    page_number: int
    text: str


class PageImageResponse(BaseModel):
    book_id: int
    page_number: int
    image_base64: str
    format: str = "PNG"


class AlignmentCheckResponse(BaseModel):
    book_id: int
    results: List[str]


class BookInfoResponse(BaseModel):
    book_id: int
    message: str


class TocResponse(BaseModel):
    book_id: int
    message: str


class AlignmentOffsetResponse(BaseModel):
    book_id: int
    message: str
    offset: Optional[int] = None


class BookListItem(BaseModel):
    book_id: int
    book_name: Optional[str] = None
    book_author: Optional[str] = None
    total_pages: Optional[int] = None  # from book_pages
    book_keywords: Optional[str] = None
    book_summary: Optional[str] = None
    book_file_name: Optional[str] = None
    book_toc_end_page: Optional[int] = None
    alignment_offset: Optional[int] = None  # from book_alignment_offset
    toc_exists: bool = False  # computed field


class BooksListResponse(BaseModel):
    books: List[BookListItem]


class ChapterItem(BaseModel):
    type: str = "chapter"
    chapter_id: int
    title: str
    start_page_number: int
    end_page_number: Optional[int] = None
    book_index_string: Optional[str] = None
    summary: Optional[str] = None


class ChaptersResponse(BaseModel):
    book_id: int
    chapters: List[ChapterItem]


class ChapterResponse(BaseModel):
    chapter: ChapterItem



class TocExistsResponse(BaseModel):
    book_id: int
    toc_exists: bool


# Section request/response models
class ExtractSectionsRequest(BaseModel):
    book_id: int = Field(..., description="ID of the book")
    chapter_id: Optional[int] = Field(default=None, description="ID of the chapter (optional)")


class UpdateSectionRequest(BaseModel):
    title: Optional[str] = Field(default=None, description="Title of the section")
    start_page_number: Optional[int] = Field(default=None, ge=0, description="Starting page number of the section")
    end_page_number: Optional[int] = Field(default=None, ge=0, description="Ending page number of the section")
    summary: Optional[str] = Field(default=None, description="Summary of the section")
    chapter_id: Optional[int] = Field(default=None, description="ID of the chapter (optional)")
    book_index_string: Optional[str] = Field(default=None, description="Index string for the section")


class SectionItem(BaseModel):
    type: str = "section"
    section_id: int
    title: str
    start_page_number: int
    end_page_number: int
    summary: Optional[str] = None
    chapter_id: Optional[int] = None
    book_index_string: Optional[str] = None
    book_id: int


class SectionsResponse(BaseModel):
    book_id: int
    sections: List[SectionItem]


class SectionResponse(BaseModel):
    section: SectionItem


class SectionMessageResponse(BaseModel):
    section_id: int
    message: str


# Page request/response models
class CreatePageRequest(BaseModel):
    book_id: int = Field(..., description="ID of the book")
    page_number: int = Field(..., ge=0, description="Page number (0-indexed)")
    summary: Optional[str] = Field(default=None, description="Summary of the page content")
    # Note: embedding, related_chapters, related_section_id are BLOB fields and not exposed via API


class UpdatePageRequest(BaseModel):
    page_number: Optional[int] = Field(default=None, ge=0, description="Page number (0-indexed)")
    summary: Optional[str] = Field(default=None, description="Summary of the page content")
    # Note: embedding, related_chapters, related_section_id are BLOB fields and not exposed via API


class PageItem(BaseModel):
    type: str = "page"
    page_id: int
    page_number: int
    summary: Optional[str] = None
    book_id: int
    # Note: embedding, related_chapters, related_section_id are BLOB fields and not exposed via API


class PagesResponse(BaseModel):
    book_id: int
    pages: List[PageItem]


class PageResponse(BaseModel):
    page: PageItem


class PageMessageResponse(BaseModel):
    page_id: int
    message: str