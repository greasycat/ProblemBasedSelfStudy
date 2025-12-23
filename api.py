import os
import tomllib
import base64
import io
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, List
from warnings import warn

from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Path as FastAPIPath
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse
from pydantic import BaseModel, Field

# Append sys.path to include the project root
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from textbook import LazyTextbookReader, LLM, TextBookContext
from textbook.context import ChapterInfo, BookInfo, SectionInfo, PageInfo

# Global instances (initialized on startup)
llm: Optional[LLM] = None
context: Optional[TextBookContext] = None
db_path: str = "textbook_context.db"
uploads_dir: str = "uploads"


def load_config() -> dict:
    """Load configuration from config.toml"""
    if not os.path.exists("config.toml"):
        warn("config.toml file not found, using default config")
        return {}
    
    try:
        with open("config.toml", "rb") as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        warn(f"Error loading config.toml file: {e}")
        return {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    global llm, context, db_path, uploads_dir
    
    config = load_config()
    db_path = config.get("db_path", "textbook_context.db")
    uploads_dir = config.get("uploads_dir", "uploads")
    
    # Ensure uploads directory exists
    Path(uploads_dir).mkdir(parents=True, exist_ok=True)
    
    llm = LLM()
    context = TextBookContext(db_path=db_path)
    context.__enter__()
    
    yield
    
    # Shutdown
    if context:
        context.__exit__(None, None, None)


app = FastAPI(title="Textbook Reader API", version="0.1.0", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
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

class UploadBookResponse(BaseModel):
    book_id: int
    message: str


class DeleteBookResponse(BaseModel):
    book_id: int
    message: str
    deleted: bool


class TocExistsResponse(BaseModel):
    book_id: int
    toc_exists: bool


# Section request/response models
class CreateSectionRequest(BaseModel):
    book_id: int = Field(..., description="ID of the book")
    title: str = Field(..., description="Title of the section")
    start_page_number: int = Field(..., ge=0, description="Starting page number of the section")
    end_page_number: int = Field(..., ge=0, description="Ending page number of the section")
    summary: Optional[str] = Field(default=None, description="Summary of the section")
    chapter_id: Optional[int] = Field(default=None, description="ID of the chapter (optional)")
    book_index_string: Optional[str] = Field(default=None, description="Index string for the section")


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


def get_pdf_path_from_book_id(book_id: int) -> Path:
    """Helper function to get pdf_path from book_id"""
    if not context:
        raise HTTPException(status_code=500, detail="Context not initialized")
    
    with context.new_session() as session:
        book = session.query(BookInfo).filter(BookInfo.book_id == book_id).first()
        if not book or not book.book_file_name:
            raise HTTPException(status_code=404, detail=f"PDF file not found for book, consider uploading the book first: {book_id}")
        return Path(uploads_dir) / Path(book.book_file_name + ".pdf") 


def get_reader(pdf_path: Path) -> LazyTextbookReader:
    """Helper function to create and enter a LazyTextbookReader context"""
    if not llm or not context:
        raise HTTPException(status_code=500, detail="LLM or Context not initialized")
    
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail=f"PDF file not found: {pdf_path}")
    
    reader = LazyTextbookReader(pdf_path, llm, context)
    return reader.__enter__()


def get_reader_by_book_id(book_id: int) -> LazyTextbookReader:
    """Helper function to create and enter a LazyTextbookReader context using book_id"""
    pdf_path = get_pdf_path_from_book_id(book_id)
    return get_reader(pdf_path)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Textbook Reader API", "version": "0.1.0"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "llm_initialized": llm is not None,
        "context_initialized": context is not None
    }


@app.post("/total-pages", response_model=TotalPagesResponse)
async def get_total_pages(request: BookIdRequest):
    """Get the total number of pages in a PDF"""
    try:
        pdf_path = get_pdf_path_from_book_id(request.book_id)
        with get_reader(pdf_path) as reader:
            total_pages = reader.get_total_pages()
            return TotalPagesResponse(
                book_id=request.book_id,
                total_pages=total_pages
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/page-text", response_model=PageTextResponse)
async def get_page_text(request: PageNumberRequest):
    """Get text content from a specific page"""
    try:
        pdf_path = get_pdf_path_from_book_id(request.book_id)
        with get_reader(pdf_path) as reader:
            text = reader.get_page_content(request.page_number)
            return PageTextResponse(
                book_id=request.book_id,
                page_number=request.page_number,
                text=text
            )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/page-image", response_model=PageImageResponse)
async def get_page_image(request: PageImageRequest):
    """Get image representation of a specific page"""
    try:
        pdf_path = get_pdf_path_from_book_id(request.book_id)
        with get_reader(pdf_path) as reader:
            img = reader.get_page_as_image(request.page_number, request.dpi)
            
            # Convert PIL Image to base64
            img_buffer = io.BytesIO()
            img.save(img_buffer, format="PNG")
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode("utf-8")
            
            return PageImageResponse(
                book_id=request.book_id,
                page_number=request.page_number,
                image_base64=img_base64,
                format="PNG"
            )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/page-image-binary")
async def get_page_image_binary(
    book_id: int = Query(..., description="ID of the book"),
    page_number: int = Query(..., ge=0, description="Page number (0-indexed)"),
    dpi: int = Query(default=150, ge=72, le=300, description="DPI for image rendering")
):
    """Get image representation of a specific page as binary PNG"""
    try:
        pdf_path = get_pdf_path_from_book_id(book_id)
        with get_reader(pdf_path) as reader:
            img = reader.get_page_as_image(page_number, dpi)
            
            # Convert PIL Image to bytes
            img_buffer = io.BytesIO()
            img.save(img_buffer, format="PNG")
            img_buffer.seek(0)
            
            return Response(
                content=img_buffer.getvalue(),
                media_type="image/png"
            )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/view-pdf")
async def view_pdf(book_id: int = Query(..., description="ID of the book")):
    """View/serve the PDF file for a book"""
    try:
        pdf_path = get_pdf_path_from_book_id(book_id)
        
        print(pdf_path)
        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=404, detail=f"PDF file not found: {pdf_path}")
        
        return FileResponse(
            path=str(pdf_path),
            media_type="application/pdf",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/update-book-info", response_model=BookInfoResponse)
async def update_book_info(request: UpdateBookInfoRequest):
    """Extract and update book information from the PDF"""
    try:
        pdf_path = get_pdf_path_from_book_id(request.book_id)
        with get_reader(pdf_path) as reader:
            reader.update_book_info(overwrite=request.overwrite)
            return BookInfoResponse(
                book_id=request.book_id,
                message="Book info updated successfully"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/check-toc-exists", response_model=TocExistsResponse)
async def check_toc_exists(book_id: int = Query(..., description="ID of the book")):
    """Check if table of contents exists for the PDF"""
    try:
        pdf_path = get_pdf_path_from_book_id(book_id)
        with get_reader(pdf_path) as reader:
            exists = reader.check_if_toc_exists()
            return TocExistsResponse(
                book_id=book_id,
                toc_exists=exists
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/update-toc", response_model=TocResponse)
async def update_toc(request: UpdateTocRequest):
    """Extract and update table of contents from the PDF"""
    try:
        pdf_path = get_pdf_path_from_book_id(request.book_id)
        with get_reader(pdf_path) as reader:
            reader.update_toc(caching=request.caching, overwrite=request.overwrite)
            return TocResponse(
                book_id=request.book_id,
                message="Table of contents updated successfully"
            )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/update-alignment-offset", response_model=AlignmentOffsetResponse)
async def update_alignment_offset(request: UpdateAlignmentOffsetRequest):
    """Update the alignment offset for page numbers"""
    try:
        pdf_path = get_pdf_path_from_book_id(request.book_id)
        with get_reader(pdf_path) as reader:
            reader.update_alignment_offset(request.page_number)
            return AlignmentOffsetResponse(
                book_id=request.book_id,
                message="Alignment offset updated successfully",
                offset=request.page_number
            )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/check-alignment-offset", response_model=AlignmentCheckResponse)
async def check_alignment_offset(request: CheckAlignmentOffsetRequest):
    """Check alignment offset by returning sample pages"""
    try:
        pdf_path = get_pdf_path_from_book_id(request.book_id)
        with get_reader(pdf_path) as reader:
            results = reader.check_alignment_offset()
            return AlignmentCheckResponse(
                book_id=request.book_id,
                results=results
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/books", response_model=BooksListResponse)
async def get_books():
    """Get all books from the database"""
    try:
        if not context:
            raise HTTPException(status_code=500, detail="Context not initialized")
        
        book_items = []
        
        with context.new_session() as session:
            # Get all books in the same session
            all_books = session.query(BookInfo).all()
            
            for book in all_books:
                try:
                    # Check if TOC exists by checking if there are chapters
                    toc_exists = False
                    if book.book_id:
                        chapters = session.query(ChapterInfo).filter(
                            ChapterInfo.book_id == book.book_id
                        ).all()
                        toc_exists = len(chapters) > 0
                    
                    book_items.append(BookListItem(
                        book_id=book.book_id,
                        book_name=book.book_name,
                        book_author=book.book_author,
                        total_pages=book.book_pages,
                        book_keywords=book.book_keywords,
                        book_summary=book.book_summary,
                        book_file_name=book.book_file_name,
                        book_toc_end_page=book.book_toc_end_page,
                        alignment_offset=book.book_alignment_offset,
                        toc_exists=toc_exists
                    ))
                except Exception as book_error:
                    # Log error for individual book but continue processing others
                    print(f"Error processing book {book.book_id}: {book_error}")
                    continue
        
        return BooksListResponse(books=book_items)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in /books endpoint: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/upload-book", response_model=UploadBookResponse)
async def upload_book(file: UploadFile = File(..., description="PDF file to upload")):
    """Upload a PDF file and create a book entry in the database"""
    global uploads_dir
    
    try:
        if not llm or not context:
            raise HTTPException(status_code=500, detail="LLM or Context not initialized")
        
        # Validate file type
        if not file.filename or not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Generate UUID for filename
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(uploads_dir, unique_filename)
        
        # Save uploaded file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Use LazyTextbookReader to create book entry
        try:
            with get_reader(Path(file_path)) as reader:
                reader.update_book_info(overwrite=False)
                
                # Get the created book info
                book_info = reader.book_info
                if not book_info or not book_info.book_id:
                    raise HTTPException(status_code=500, detail="Failed to create book entry")
                
                return UploadBookResponse(
                    book_id=book_info.book_id,
                    message="Book uploaded and created successfully"
                )
        except Exception as reader_error:
            # If book creation fails, clean up the uploaded file
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"Failed to create book entry: {str(reader_error)}")
            
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in /upload-book endpoint: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.delete("/delete-book", response_model=DeleteBookResponse)
async def delete_book(book_id: int = Query(..., description="ID of the book to delete")):
    """Delete a book from both the database and the file system"""
    try:
        if not context:
            raise HTTPException(status_code=500, detail="Context not initialized")
        
        # Get pdf_path before deleting
        pdf_path = get_pdf_path_from_book_id(book_id)
        
        # Delete from database
        with context.new_session() as session:
            book = session.query(BookInfo).filter(BookInfo.book_id == book_id).first()
            if not book:
                raise HTTPException(status_code=404, detail=f"Book not found: {book_id}")
            
            session.delete(book)
            session.commit()
        
        # Delete file from file system if it exists
        file_deleted = False
        if os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
                file_deleted = True
            except OSError as e:
                # Log error but don't fail if file deletion fails
                print(f"Warning: Failed to delete file {pdf_path}: {e}")
        else:
            print(f"File not found: {pdf_path}")
        
        return DeleteBookResponse(
            book_id=book_id,
            message="Book deleted successfully" + (f" (file {'deleted' if file_deleted else 'not found'})" if not file_deleted else ""),
            deleted=True
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in /delete-book endpoint: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/chapters", response_model=ChaptersResponse)
async def get_chapters(book_id: int = Query(..., description="ID of the book")):
    """Get all chapters for a book by book_id"""
    try:
        if not context:
            raise HTTPException(status_code=500, detail="Context not initialized")

        with context.new_session() as session:
            # Get chapters for this book
            chapters = session.query(ChapterInfo).filter(
                ChapterInfo.book_id == book_id
            ).order_by(ChapterInfo.start_page_number).all()
            
            chapter_items = [
                ChapterItem(
                    chapter_id=ch.chapter_id,
                    title=ch.title,
                    start_page_number=ch.start_page_number,
                    end_page_number=ch.end_page_number,
                    book_index_string=ch.book_index_string
                )
                for ch in chapters
            ]
            
            return ChaptersResponse(
                book_id=book_id,
                chapters=chapter_items
            )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in /chapters endpoint: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/chapters/{chapter_id}", response_model=ChapterResponse)
async def get_chapter(chapter_id: int = FastAPIPath(..., ge=0, description="ID of the chapter")):
    """Get a specific chapter by ID"""
    try:
        if not context:
            raise HTTPException(status_code=500, detail="Context not initialized")
        
        with context.new_session() as session:
            chapter = session.query(ChapterInfo).filter(ChapterInfo.chapter_id == chapter_id).first()
            if not chapter:
                raise HTTPException(status_code=404, detail=f"Chapter not found: {chapter_id}")
            
            return ChapterResponse(
                chapter=ChapterItem(
                    chapter_id=chapter.chapter_id,
                    title=chapter.title,
                    start_page_number=chapter.start_page_number,
                    end_page_number=chapter.end_page_number,
                    book_index_string=chapter.book_index_string
                )
            )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in /chapters/{chapter_id} GET endpoint: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")



# Section CRUD endpoints
@app.post("/sections", response_model=SectionMessageResponse)
async def create_section(request: CreateSectionRequest):
    """Create a new section"""
    try:
        if not context:
            raise HTTPException(status_code=500, detail="Context not initialized")
        
        with context.new_session() as session:
            # Verify book exists
            book = session.query(BookInfo).filter(BookInfo.book_id == request.book_id).first()
            if not book:
                raise HTTPException(status_code=404, detail=f"Book not found: {request.book_id}")
            
            # Verify chapter exists if provided
            if request.chapter_id is not None:
                chapter = session.query(ChapterInfo).filter(ChapterInfo.chapter_id == request.chapter_id).first()
                if not chapter:
                    raise HTTPException(status_code=404, detail=f"Chapter not found: {request.chapter_id}")
            
            # Check for duplicate title within the same book
            existing = session.query(SectionInfo).filter(
                SectionInfo.book_id == request.book_id,
                SectionInfo.title == request.title
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail=f"Section with title '{request.title}' already exists for this book")
            
            # Create new section
            section = SectionInfo(
                book_id=request.book_id,
                title=request.title,
                start_page_number=request.start_page_number,
                end_page_number=request.end_page_number,
                summary=request.summary,
                chapter_id=request.chapter_id,
                book_index_string=request.book_index_string
            )
            
            session.add(section)
            session.commit()
            session.refresh(section)
            
            return SectionMessageResponse(
                section_id=section.section_id,
                message="Section created successfully"
            )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in /sections POST endpoint: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/sections", response_model=SectionsResponse)
async def get_sections(
    book_id: int = Query(..., description="ID of the book"),
    chapter_id: Optional[int] = Query(default=None, description="Optional chapter ID to filter sections"),
):
    """Get all sections for a book, optionally filtered by chapter"""
    try:
        if not context:
            raise HTTPException(status_code=500, detail="Context not initialized")
        
        with context.new_session() as session:
            query = session.query(SectionInfo).filter(SectionInfo.book_id == book_id)
            
            if chapter_id is not None:
                query = query.filter(SectionInfo.chapter_id == chapter_id)
            
            sections = query.order_by(SectionInfo.start_page_number).all()
            
            section_items = [
                SectionItem(
                    section_id=sec.section_id,
                    title=sec.title,
                    start_page_number=sec.start_page_number,
                    end_page_number=sec.end_page_number,
                    summary=sec.summary,
                    chapter_id=sec.chapter_id,
                    book_index_string=sec.book_index_string,
                    book_id=sec.book_id
                )
                for sec in sections
            ]
            
            return SectionsResponse(
                book_id=book_id,
                sections=section_items
            )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in /sections GET endpoint: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/sections/{section_id}", response_model=SectionResponse)
async def get_section(section_id: int = FastAPIPath(..., ge=0, description="ID of the section")):
    """Get a specific section by ID"""
    try:
        if not context:
            raise HTTPException(status_code=500, detail="Context not initialized")
        
        with context.new_session() as session:
            section = session.query(SectionInfo).filter(SectionInfo.section_id == section_id).first()
            if not section:
                raise HTTPException(status_code=404, detail=f"Section not found: {section_id}")
            
            return SectionResponse(
                section=SectionItem(
                    section_id=section.section_id,
                    title=section.title,
                    start_page_number=section.start_page_number,
                    end_page_number=section.end_page_number,
                    summary=section.summary,
                    chapter_id=section.chapter_id,
                    book_index_string=section.book_index_string,
                    book_id=section.book_id
                )
            )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in /sections/{section_id} GET endpoint: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.put("/sections/{section_id}", response_model=SectionMessageResponse)
async def update_section(request: UpdateSectionRequest, section_id: int = FastAPIPath(..., ge=0, description="ID of the section")):
    """Update a section"""
    try:
        if not context:
            raise HTTPException(status_code=500, detail="Context not initialized")
        
        with context.new_session() as session:
            section = session.query(SectionInfo).filter(SectionInfo.section_id == section_id).first()
            if not section:
                raise HTTPException(status_code=404, detail=f"Section not found: {section_id}")
            
            # Verify chapter exists if provided
            if request.chapter_id is not None:
                chapter = session.query(ChapterInfo).filter(ChapterInfo.chapter_id == request.chapter_id).first()
                if not chapter:
                    raise HTTPException(status_code=404, detail=f"Chapter not found: {request.chapter_id}")
            
            # Check for duplicate title if title is being updated
            if request.title is not None and request.title != section.title:
                existing = session.query(SectionInfo).filter(
                    SectionInfo.book_id == section.book_id,
                    SectionInfo.title == request.title,
                    SectionInfo.section_id != section_id
                ).first()
                if existing:
                    raise HTTPException(status_code=400, detail=f"Section with title '{request.title}' already exists for this book")
            
            # Update fields
            if request.title is not None:
                section.title = request.title
            if request.start_page_number is not None:
                section.start_page_number = request.start_page_number
            if request.end_page_number is not None:
                section.end_page_number = request.end_page_number
            if request.summary is not None:
                section.summary = request.summary
            if request.chapter_id is not None:
                section.chapter_id = request.chapter_id
            if request.book_index_string is not None:
                section.book_index_string = request.book_index_string
            
            session.commit()
            
            return SectionMessageResponse(
                section_id=section_id,
                message="Section updated successfully"
            )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in /sections/{section_id} PUT endpoint: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.delete("/sections/{section_id}", response_model=SectionMessageResponse)
async def delete_section(section_id: int = FastAPIPath(..., ge=0, description="ID of the section")):
    """Delete a section"""
    try:
        if not context:
            raise HTTPException(status_code=500, detail="Context not initialized")
        
        with context.new_session() as session:
            section = session.query(SectionInfo).filter(SectionInfo.section_id == section_id).first()
            if not section:
                raise HTTPException(status_code=404, detail=f"Section not found: {section_id}")
            
            session.delete(section)
            session.commit()
            
            return SectionMessageResponse(
                section_id=section_id,
                message="Section deleted successfully"
            )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in /sections/{section_id} DELETE endpoint: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Page CRUD endpoints
@app.post("/pages", response_model=PageMessageResponse)
async def create_page(request: CreatePageRequest):
    """Create a new page info entry"""
    try:
        if not context:
            raise HTTPException(status_code=500, detail="Context not initialized")
        
        with context.new_session() as session:
            # Verify book exists
            book = session.query(BookInfo).filter(BookInfo.book_id == request.book_id).first()
            if not book:
                raise HTTPException(status_code=404, detail=f"Book not found: {request.book_id}")
            
            # Check for duplicate page_number within the same book
            existing = session.query(PageInfo).filter(
                PageInfo.book_id == request.book_id,
                PageInfo.page_number == request.page_number
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail=f"Page with page_number {request.page_number} already exists for this book")
            
            # Create new page
            page = PageInfo(
                book_id=request.book_id,
                page_number=request.page_number,
                summary=request.summary
            )
            
            session.add(page)
            session.commit()
            session.refresh(page)
            
            return PageMessageResponse(
                page_id=page.page_id,
                message="Page created successfully"
            )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in /pages POST endpoint: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/pages", response_model=PagesResponse)
async def get_pages(book_id: int = Query(..., description="ID of the book")):
    """Get all pages for a book"""
    try:
        if not context:
            raise HTTPException(status_code=500, detail="Context not initialized")
        
        with context.new_session() as session:
            pages = session.query(PageInfo).filter(
                PageInfo.book_id == book_id
            ).order_by(PageInfo.page_number).all()
            
            page_items = [
                PageItem(
                    page_id=page.page_id,
                    page_number=page.page_number,
                    summary=page.summary,
                    book_id=page.book_id
                )
                for page in pages
            ]
            
            return PagesResponse(
                book_id=book_id,
                pages=page_items
            )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in /pages GET endpoint: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/pages/{page_id}", response_model=PageResponse)
async def get_page(page_id: int):
    """Get a specific page by ID"""
    try:
        if not context:
            raise HTTPException(status_code=500, detail="Context not initialized")
        
        with context.new_session() as session:
            page = session.query(PageInfo).filter(PageInfo.page_id == page_id).first()
            if not page:
                raise HTTPException(status_code=404, detail=f"Page not found: {page_id}")
            
            return PageResponse(
                page=PageItem(
                    page_id=page.page_id,
                    page_number=page.page_number,
                    summary=page.summary,
                    book_id=page.book_id
                )
            )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in /pages/{page_id} GET endpoint: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.put("/pages/{page_id}", response_model=PageMessageResponse)
async def update_page(page_id: int, request: UpdatePageRequest):
    """Update a page"""
    try:
        if not context:
            raise HTTPException(status_code=500, detail="Context not initialized")
        
        with context.new_session() as session:
            page = session.query(PageInfo).filter(PageInfo.page_id == page_id).first()
            if not page:
                raise HTTPException(status_code=404, detail=f"Page not found: {page_id}")
            
            # Check for duplicate page_number if page_number is being updated
            if request.page_number is not None and request.page_number != page.page_number:
                existing = session.query(PageInfo).filter(
                    PageInfo.book_id == page.book_id,
                    PageInfo.page_number == request.page_number,
                    PageInfo.page_id != page_id
                ).first()
                if existing:
                    raise HTTPException(status_code=400, detail=f"Page with page_number {request.page_number} already exists for this book")
            
            # Update fields
            if request.page_number is not None:
                page.page_number = request.page_number
            if request.summary is not None:
                page.summary = request.summary
            
            session.commit()
            
            return PageMessageResponse(
                page_id=page_id,
                message="Page updated successfully"
            )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in /pages/{page_id} PUT endpoint: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.delete("/pages/{page_id}", response_model=PageMessageResponse)
async def delete_page(page_id: int):
    """Delete a page"""
    try:
        if not context:
            raise HTTPException(status_code=500, detail="Context not initialized")
        
        with context.new_session() as session:
            page = session.query(PageInfo).filter(PageInfo.page_id == page_id).first()
            if not page:
                raise HTTPException(status_code=404, detail=f"Page not found: {page_id}")
            
            session.delete(page)
            session.commit()
            
            return PageMessageResponse(
                page_id=page_id,
                message="Page deleted successfully"
            )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in /pages/{page_id} DELETE endpoint: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765)

