# Standard library
import io
import os
import sys
import asyncio
from pathlib import Path
from typing import Optional, List
import tomllib
import base64
import uuid
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor


# Logging
import logging
import structlog
from structlog.stdlib import ProcessorFormatter
from structlog.types import Processor

# FastAPI
from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Path as FastAPIPath
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse

# Textbook
from textbook import LazyTextbookReader, LLM, TextBookDatabase
from textbook.database import ChapterInfo, BookInfo, SectionInfo, PageInfo

# API models
from api.models import BookIdRequest, PageNumberRequest, PageImageRequest, UpdateBookInfoRequest, UpdateTocRequest, UpdateAlignmentOffsetRequest, UpdateBookFieldsRequest, CheckAlignmentOffsetRequest, TotalPagesResponse, PageTextResponse, PageImageResponse, BookInfoResponse, TocExistsResponse, TocResponse, AlignmentOffsetResponse, AlignmentCheckResponse, BooksListResponse, ChaptersResponse, ChapterResponse, UploadBookResponse, DeleteBookResponse, SectionMessageResponse, UpdateSectionRequest, SectionItem, SectionsResponse, SectionResponse, PageMessageResponse, CreatePageRequest, UpdatePageRequest, PageItem, PagesResponse, PageResponse, BookListItem, ChapterItem

# Global instances (initialized on startup)
struct_logger: Optional[structlog.BoundLogger] = None
llm: Optional[LLM] = None
database: Optional[TextBookDatabase] = None
db_path: str = "textbook_context.db"
uploads_dir: str = "uploads"
executor: Optional[ThreadPoolExecutor] = None



shared_processors: List[Processor] = [
    structlog.stdlib.add_log_level,
    structlog.processors.CallsiteParameterAdder(
        {
            structlog.processors.CallsiteParameter.FILENAME,
            structlog.processors.CallsiteParameter.LINENO,
        }
    ),
    structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S.%f"),
]

structlog_processors = shared_processors + []
# Remove _record & _from_structlog.
logging_processors: List[Processor] = [ProcessorFormatter.remove_processors_meta]

if sys.stderr.isatty():
    console_renderer = structlog.dev.ConsoleRenderer()
    logging_processors.append(console_renderer)
    structlog_processors.append(console_renderer)
else:
    json_renderer = structlog.processors.JSONRenderer(indent=1, sort_keys=True)
    structlog_processors.append(json_renderer)
    logging_processors.append(json_renderer)

structlog.configure(
    processors=structlog_processors,
    wrapper_class=structlog.stdlib.BoundLogger,
    # logger_factory=structlog.stdlib.LoggerFactory(),
    logger_factory=structlog.PrintLoggerFactory(sys.stderr),
    context_class=dict,
    cache_logger_on_first_use=True,
)


formatter = ProcessorFormatter(
    # These run ONLY on `logging` entries that do NOT originate within
    # structlog.
    foreign_pre_chain=shared_processors,
    # These run on ALL entries after the pre_chain is done.
    processors=logging_processors,
)

handler = logging.StreamHandler(sys.stderr)
# Use OUR `ProcessorFormatter` to format all `logging` entries.
handler.setFormatter(formatter)
logging.basicConfig(handlers=[handler], level=logging.INFO)

logger = logging.getLogger("uvicorn.error")
logger.handlers = [handler]
logger.propagate = False


def load_config() -> dict:
    """Load configuration from config.toml"""
    if not os.path.exists("config.toml"):
        print("config.toml file not found, using default config")
        return {}
    
    try:
        with open("config.toml", "rb") as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        print(f"Error loading config.toml file: {e}")
        return {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    global llm, database, db_path, uploads_dir, struct_logger, executor
    
    config = load_config()
    db_path = config.get("db_path", "textbook_context.db")
    uploads_dir = config.get("uploads_dir", "uploads")
    
    # Ensure uploads directory exists
    Path(uploads_dir).mkdir(parents=True, exist_ok=True)

    struct_logger = structlog.get_logger()
    
    # Initialize thread pool executor for blocking operations
    executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="api-worker")
    
    llm = LLM()
    database = TextBookDatabase(db_path=db_path)
    database.__enter__()
    
    yield
    
    # Shutdown
    if executor:
        executor.shutdown(wait=True)
    if database:
        database.__exit__(None, None, None)

app = FastAPI(title="Textbook Reader API", version="0.1.0", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




def get_pdf_path_from_book_id(book_id: int) -> Path:
    """Helper function to get pdf_path from book_id"""
    if not database:
        raise HTTPException(status_code=500, detail="Context not initialized")
    
    with database.new_session() as session:
        book = session.query(BookInfo).filter(BookInfo.book_id == book_id).first()
        if not book or not book.book_file_name:
            raise HTTPException(status_code=404, detail=f"PDF file not found for book, consider uploading the book first: {book_id}")
        return Path(uploads_dir) / Path(book.book_file_name + ".pdf") 


def get_reader(pdf_path: Path) -> LazyTextbookReader:
    """Helper function to create and enter a LazyTextbookReader context"""
    if not llm or not database:
        raise HTTPException(status_code=500, detail="LLM or Context not initialized")
    
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail=f"PDF file not found: {pdf_path}")
    
    reader = LazyTextbookReader(pdf_path, llm, database)
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
    if struct_logger:
        struct_logger.info("Health check endpoint called")

    return {
        "status": "healthy",
        "llm_initialized": llm is not None,
        "context_initialized": database is not None
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
    if struct_logger:
        struct_logger.info(f"Updating book info for book {request.book_id}", request=request)

    """Extract and update book information from the PDF"""
    try:
        if not executor:
            raise HTTPException(status_code=500, detail="Executor not initialized")
        
        pdf_path = get_pdf_path_from_book_id(request.book_id)
        
        # Define a blocking function to run in executor
        def update_book_info_blocking():
            with get_reader(pdf_path) as reader:
                reader.update_book_info()
        
        # Run the blocking operation in executor to avoid blocking the event loop
        await asyncio.get_event_loop().run_in_executor(executor, update_book_info_blocking)
        
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
    if struct_logger:
        struct_logger.info(f"Updating table of contents for book {request.book_id}", request=request)
    try:
        if not executor:
            raise HTTPException(status_code=500, detail="Executor not initialized")
        
        pdf_path = get_pdf_path_from_book_id(request.book_id)
        
        # Define a blocking function to run in executor
        def update_toc_blocking():
            with get_reader(pdf_path) as reader:
                if not reader.check_if_book_exists_and_load():
                    raise HTTPException(status_code=404, detail="Book not found")
                reader.update_toc(caching=request.caching, overwrite=request.overwrite)
        
        # Run the blocking operation in executor to avoid blocking the event loop
        await asyncio.get_event_loop().run_in_executor(executor, update_toc_blocking)
        
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
        if not executor:
            raise HTTPException(status_code=500, detail="Executor not initialized")
        
        pdf_path = get_pdf_path_from_book_id(request.book_id)
        
        # Define a blocking function to run in executor
        def update_alignment_offset_blocking():
            with get_reader(pdf_path) as reader:
                reader.update_alignment_offset(request.page_number)
        
        # Run the blocking operation in executor to avoid blocking the event loop
        await asyncio.get_event_loop().run_in_executor(executor, update_alignment_offset_blocking)
        
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


@app.put("/books/{book_id}", response_model=BookInfoResponse)
async def update_book_fields(book_id: int, request: UpdateBookFieldsRequest):
    """Update book fields directly (title, author, keywords, alignment offset)"""
    try:
        if not database:
            raise HTTPException(status_code=500, detail="Context not initialized")
        
        with database.new_session() as session:
            book = session.query(BookInfo).filter(BookInfo.book_id == book_id).first()
            if not book:
                raise HTTPException(status_code=404, detail=f"Book not found: {book_id}")
            
            # Update fields if provided
            if request.book_name is not None:
                book.book_name = request.book_name
            if request.book_author is not None:
                book.book_author = request.book_author
            if request.book_keywords is not None:
                book.book_keywords = request.book_keywords
            if request.alignment_offset is not None:
                book.book_alignment_offset = request.alignment_offset
            
            session.commit()
            
            return BookInfoResponse(
                book_id=book_id,
                message="Book fields updated successfully"
            )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in /books/{book_id} PUT endpoint: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/check-alignment-offset", response_model=AlignmentCheckResponse)
async def check_alignment_offset(request: CheckAlignmentOffsetRequest):
    """Check alignment offset by returning sample pages"""
    try:
        if not executor:
            raise HTTPException(status_code=500, detail="Executor not initialized")
        
        pdf_path = get_pdf_path_from_book_id(request.book_id)
        
        # Define a blocking function to run in executor
        def check_alignment_offset_blocking():
            with get_reader(pdf_path) as reader:
                return reader.check_alignment_offset()
        
        # Run the blocking operation in executor to avoid blocking the event loop
        results = await asyncio.get_event_loop().run_in_executor(executor, check_alignment_offset_blocking)
        
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
        if not database:
            raise HTTPException(status_code=500, detail="Context not initialized")
        
        book_items = []
        
        with database.new_session() as session:
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
        if not llm or not database:
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
            if not executor:
                raise HTTPException(status_code=500, detail="Executor not initialized")
            
            pdf_path = Path(file_path)
            
            # Define a blocking function to run in executor
            def update_book_info_blocking():
                with get_reader(pdf_path) as reader:
                    reader.update_book_info()
                    return reader.book_info
            
            # Run the blocking operation in executor to avoid blocking the event loop
            book_info = await asyncio.get_event_loop().run_in_executor(executor, update_book_info_blocking)
            
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
        if not database:
            raise HTTPException(status_code=500, detail="Context not initialized")
        
        # Get pdf_path before deleting
        pdf_path = get_pdf_path_from_book_id(book_id)
        
        # Delete from database
        with database.new_session() as session:
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
        if not database:
            raise HTTPException(status_code=500, detail="Context not initialized")

        with database.new_session() as session:
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
        if not database:
            raise HTTPException(status_code=500, detail="Context not initialized")
        
        with database.new_session() as session:
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



# # Section CRUD endpoints
# @app.post("/sections", response_model=SectionMessageResponse)
# async def extract_sections(request: ExtractSectionsRequest):
#     """Create a new section"""
#     try:
#         if not database:
#             raise HTTPException(status_code=500, detail="Context not initialized")
        
#         with database.new_session() as session:
#             # Verify book exists
#             book = session.query(BookInfo).filter(BookInfo.book_id == request.book_id).first()
#             if not book:
#                 raise HTTPException(status_code=404, detail=f"Book not found: {request.book_id}")
            
#             # Verify chapter exists if provided
#             if request.chapter_id is not None:
#                 chapter = session.query(ChapterInfo).filter(ChapterInfo.chapter_id == request.chapter_id).first()
#                 if not chapter:
#                     raise HTTPException(status_code=404, detail=f"Chapter not found: {request.chapter_id}")
            
#             return SectionMessageResponse(
#                 section_id=section.section_id,
#                 message="Section created successfully"
#             )
#     except HTTPException:
#         raise
#     except Exception as e:
#         import traceback
#         error_trace = traceback.format_exc()
#         print(f"Error in /sections POST endpoint: {error_trace}")
#         raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/sections", response_model=SectionsResponse)
async def get_sections(
    book_id: int = Query(..., description="ID of the book"),
    chapter_id: Optional[int] = Query(default=None, description="Optional chapter ID to filter sections"),
):
    """Get all sections for a book, optionally filtered by chapter"""
    try:
        if not database:
            raise HTTPException(status_code=500, detail="Context not initialized")
        
        with database.new_session() as session:
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
        if not database:
            raise HTTPException(status_code=500, detail="Context not initialized")
        
        with database.new_session() as session:
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
        if not database:
            raise HTTPException(status_code=500, detail="Context not initialized")
        
        with database.new_session() as session:
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
        if not database:
            raise HTTPException(status_code=500, detail="Context not initialized")
        
        with database.new_session() as session:
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
        if not database:
            raise HTTPException(status_code=500, detail="Context not initialized")
        
        with database.new_session() as session:
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
        if not database:
            raise HTTPException(status_code=500, detail="Context not initialized")
        
        with database.new_session() as session:
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
        if not database:
            raise HTTPException(status_code=500, detail="Context not initialized")
        
        with database.new_session() as session:
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
        if not database:
            raise HTTPException(status_code=500, detail="Context not initialized")
        
        with database.new_session() as session:
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
        if not database:
            raise HTTPException(status_code=500, detail="Context not initialized")
        
        with database.new_session() as session:
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
