import os
import tomllib
import base64
import io
from typing import Optional, List
from warnings import warn

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

# Append sys.path to include the project root
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from textbook import LazyTextbookReader, LLM, TextBookContext
from textbook.context import ChapterInfo, BookInfo

app = FastAPI(title="Textbook Reader API", version="0.1.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances (initialized on startup)
llm: Optional[LLM] = None
context: Optional[TextBookContext] = None
db_path: str = "textbook_context.db"


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


@app.on_event("startup")
async def startup_event():
    """Initialize LLM and TextBookContext on startup"""
    global llm, context, db_path
    
    config = load_config()
    db_path = config.get("db_path", "textbook_context.db")
    
    llm = LLM()
    context = TextBookContext(db_path=db_path)
    context.__enter__()


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    global context
    if context:
        context.__exit__(None, None, None)


# Request/Response models
class PDFPathRequest(BaseModel):
    pdf_path: str = Field(..., description="Path to the PDF file")


class PageNumberRequest(BaseModel):
    pdf_path: str = Field(..., description="Path to the PDF file")
    page_number: int = Field(..., ge=0, description="Page number (0-indexed)")


class PageImageRequest(BaseModel):
    pdf_path: str = Field(..., description="Path to the PDF file")
    page_number: int = Field(..., ge=0, description="Page number (0-indexed)")
    dpi: int = Field(default=150, ge=72, le=300, description="DPI for image rendering")


class UpdateBookInfoRequest(BaseModel):
    pdf_path: str = Field(..., description="Path to the PDF file")
    overwrite: bool = Field(default=False, description="Whether to overwrite existing book info")


class UpdateTocRequest(BaseModel):
    pdf_path: str = Field(..., description="Path to the PDF file")
    caching: bool = Field(default=True, description="Whether to cache TOC results")
    overwrite: bool = Field(default=False, description="Whether to overwrite existing TOC")


class UpdateAlignmentOffsetRequest(BaseModel):
    pdf_path: str = Field(..., description="Path to the PDF file")
    page_number: int = Field(..., ge=0, description="Page number for alignment offset")


class CheckAlignmentOffsetRequest(BaseModel):
    pdf_path: str = Field(..., description="Path to the PDF file")


class TotalPagesResponse(BaseModel):
    pdf_path: str
    total_pages: int


class PageTextResponse(BaseModel):
    pdf_path: str
    page_number: int
    text: str


class PageImageResponse(BaseModel):
    pdf_path: str
    page_number: int
    image_base64: str
    format: str = "PNG"


class AlignmentCheckResponse(BaseModel):
    pdf_path: str
    results: List[str]


class BookInfoResponse(BaseModel):
    pdf_path: str
    message: str


class TocResponse(BaseModel):
    pdf_path: str
    message: str


class AlignmentOffsetResponse(BaseModel):
    pdf_path: str
    message: str
    offset: Optional[int] = None


class BookListItem(BaseModel):
    book_id: int
    pdf_path: str  # from book_file_name
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


def get_reader(pdf_path: str) -> LazyTextbookReader:
    """Helper function to create and enter a LazyTextbookReader context"""
    if not llm or not context:
        raise HTTPException(status_code=500, detail="LLM or Context not initialized")
    
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail=f"PDF file not found: {pdf_path}")
    
    reader = LazyTextbookReader(pdf_path, llm, context)
    return reader.__enter__()


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
async def get_total_pages(request: PDFPathRequest):
    """Get the total number of pages in a PDF"""
    try:
        with get_reader(request.pdf_path) as reader:
            total_pages = reader.get_total_pages()
            return TotalPagesResponse(
                pdf_path=request.pdf_path,
                total_pages=total_pages
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/page-text", response_model=PageTextResponse)
async def get_page_text(request: PageNumberRequest):
    """Get text content from a specific page"""
    try:
        with get_reader(request.pdf_path) as reader:
            text = reader.get_page_content(request.page_number)
            return PageTextResponse(
                pdf_path=request.pdf_path,
                page_number=request.page_number,
                text=text
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/page-image", response_model=PageImageResponse)
async def get_page_image(request: PageImageRequest):
    """Get image representation of a specific page"""
    try:
        with get_reader(request.pdf_path) as reader:
            img = reader.get_page_as_image(request.page_number, request.dpi)
            
            # Convert PIL Image to base64
            img_buffer = io.BytesIO()
            img.save(img_buffer, format="PNG")
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode("utf-8")
            
            return PageImageResponse(
                pdf_path=request.pdf_path,
                page_number=request.page_number,
                image_base64=img_base64,
                format="PNG"
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/page-image-binary")
async def get_page_image_binary(
    pdf_path: str = Query(..., description="Path to the PDF file"),
    page_number: int = Query(..., ge=0, description="Page number (0-indexed)"),
    dpi: int = Query(default=150, ge=72, le=300, description="DPI for image rendering")
):
    """Get image representation of a specific page as binary PNG"""
    try:
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
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/update-book-info", response_model=BookInfoResponse)
async def update_book_info(request: UpdateBookInfoRequest):
    """Extract and update book information from the PDF"""
    try:
        with get_reader(request.pdf_path) as reader:
            reader.update_book_info(overwrite=request.overwrite)
            return BookInfoResponse(
                pdf_path=request.pdf_path,
                message="Book info updated successfully"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/check-toc-exists")
async def check_toc_exists(pdf_path: str = Query(..., description="Path to the PDF file")):
    """Check if table of contents exists for the PDF"""
    try:
        with get_reader(pdf_path) as reader:
            exists = reader.check_if_toc_exists()
            return {
                "pdf_path": pdf_path,
                "toc_exists": exists
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/update-toc", response_model=TocResponse)
async def update_toc(request: UpdateTocRequest):
    """Extract and update table of contents from the PDF"""
    try:
        with get_reader(request.pdf_path) as reader:
            reader.update_toc(caching=request.caching, overwrite=request.overwrite)
            return TocResponse(
                pdf_path=request.pdf_path,
                message="Table of contents updated successfully"
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/update-alignment-offset", response_model=AlignmentOffsetResponse)
async def update_alignment_offset(request: UpdateAlignmentOffsetRequest):
    """Update the alignment offset for page numbers"""
    try:
        with get_reader(request.pdf_path) as reader:
            reader.update_alignment_offset(request.page_number)
            return AlignmentOffsetResponse(
                pdf_path=request.pdf_path,
                message="Alignment offset updated successfully",
                offset=request.page_number
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/check-alignment-offset", response_model=AlignmentCheckResponse)
async def check_alignment_offset(request: CheckAlignmentOffsetRequest):
    """Check alignment offset by returning sample pages"""
    try:
        with get_reader(request.pdf_path) as reader:
            results = reader.check_alignment_offset()
            return AlignmentCheckResponse(
                pdf_path=request.pdf_path,
                results=results
            )
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
                    
                    # Use book_file_name as pdf_path, or fallback to empty string
                    pdf_path = book.book_file_name or ""
                    
                    book_items.append(BookListItem(
                        book_id=book.book_id,
                        pdf_path=pdf_path,
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765)

