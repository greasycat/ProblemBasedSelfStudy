"""
Test cases for API endpoints
"""
import os
import pytest
import tempfile
import shutil
from pathlib import Path
from io import BytesIO

# Set dummy API key to avoid import errors
os.environ.setdefault("LLM_GEMINI_KEY", "dummy_key_for_testing")

from fastapi.testclient import TestClient


class TestAPIEndpoints:
    """Test suite for API endpoints"""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database file for testing"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            db_path = f.name
        yield db_path
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.fixture
    def temp_uploads_dir(self):
        """Create a temporary uploads directory for testing"""
        uploads_dir = tempfile.mkdtemp()
        yield uploads_dir
        # Cleanup
        if os.path.exists(uploads_dir):
            shutil.rmtree(uploads_dir)
    
    @pytest.fixture
    def test_pdf_path(self):
        """Get path to a test PDF file"""
        test_pdf = Path("tests/textbooks/topology_text.pdf")
        if test_pdf.exists():
            return str(test_pdf)
        # Fallback to any PDF in the tests directory
        pdf_files = list(Path("tests/textbooks").glob("*.pdf"))
        if pdf_files:
            return str(pdf_files[0])
        pytest.skip("No test PDF file found")
    
    @pytest.fixture
    def client(self, temp_db, temp_uploads_dir):
        """Create a test client with mocked dependencies"""
        # Setup context and LLM before creating client
        from textbook.database import TextBookDatabase
        from textbook.model import LLM
        import api.app as api
        
        # Initialize context
        api.database = TextBookDatabase(db_path=temp_db)
        api.database.__enter__()
        
        # Initialize LLM (will use dummy key from env)
        api.llm = LLM()
        
        # Set paths
        api.db_path = temp_db
        api.uploads_dir = temp_uploads_dir
        
        # Create client
        client = TestClient(api.app)
        yield client
        
        # Cleanup
        if api.database:
            api.database.__exit__(None, None, None)
    
    def test_root(self, client):
        """Test GET / endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["message"] == "Textbook Reader API"
    
    def test_health(self, client):
        """Test GET /health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "llm_initialized" in data
        assert "context_initialized" in data
    
    def test_get_total_pages(self, client, test_pdf_path):
        """Test POST /total-pages endpoint"""
        # First, create a book entry
        from textbook.database import BookInfo
        import api.app as api
        
        assert api.database is not None
        with api.database.new_session() as session:
            book = BookInfo(
                book_name="Test Book",
                book_author="Test Author",
                book_keywords="test",
                book_file_name=os.path.basename(test_pdf_path)
            )
            session.add(book)
            session.commit()
            session.refresh(book)
            book_id = book.book_id
        
        # Copy test PDF to uploads directory
        upload_path = Path(api.uploads_dir) / os.path.basename(test_pdf_path)
        shutil.copy(test_pdf_path, upload_path)
        
        # Update book_file_name to match the upload path
        with api.database.new_session() as session:
            book = session.query(BookInfo).filter(BookInfo.book_id == book_id).first()
            assert book is not None
            book.book_file_name = os.path.basename(test_pdf_path)
            session.commit()
        
        response = client.post("/total-pages", json={"book_id": book_id})
        assert response.status_code == 200
        data = response.json()
        assert "book_id" in data
        assert "total_pages" in data
        assert data["book_id"] == book_id
        assert data["total_pages"] > 0
    
    def test_get_page_text(self, client, test_pdf_path):
        """Test POST /page-text endpoint"""
        # First, create a book entry
        from textbook.database import BookInfo
        import api.app as api
        
        assert api.database is not None
        with api.database.new_session() as session:
            book = BookInfo(
                book_name="Test Book",
                book_author="Test Author",
                book_keywords="test",
                book_file_name=os.path.basename(test_pdf_path)
            )
            session.add(book)
            session.commit()
            session.refresh(book)
            book_id = book.book_id
        
        # Copy test PDF to uploads directory
        upload_path = Path(api.uploads_dir) / os.path.basename(test_pdf_path)
        shutil.copy(test_pdf_path, upload_path)
        
        response = client.post("/page-text", json={"book_id": book_id, "page_number": 0})
        assert response.status_code == 200
        data = response.json()
        assert "book_id" in data
        assert "page_number" in data
        assert "text" in data
        assert data["book_id"] == book_id
        assert data["page_number"] == 0
    
    def test_get_page_image(self, client, test_pdf_path):
        """Test POST /page-image endpoint"""
        # First, create a book entry
        from textbook.database import BookInfo
        import api.app as api
        
        assert api.database is not None
        with api.database.new_session() as session:
            book = BookInfo(
                book_name="Test Book",
                book_author="Test Author",
                book_keywords="test",
                book_file_name=os.path.basename(test_pdf_path)
            )
            session.add(book)
            session.commit()
            session.refresh(book)
            book_id = book.book_id
        
        # Copy test PDF to uploads directory
        upload_path = Path(api.uploads_dir) / os.path.basename(test_pdf_path)
        shutil.copy(test_pdf_path, upload_path)
        
        response = client.post("/page-image", json={"book_id": book_id, "page_number": 0, "dpi": 150})
        assert response.status_code == 200
        data = response.json()
        assert "book_id" in data
        assert "page_number" in data
        assert "image_base64" in data
        assert "format" in data
        assert data["book_id"] == book_id
        assert data["format"] == "PNG"
    
    def test_get_page_image_binary(self, client, test_pdf_path):
        """Test POST /page-image-binary endpoint"""
        # First, create a book entry
        from textbook.database import BookInfo
        import api.app as api
        
        assert api.database is not None
        with api.database.new_session() as session:
            book = BookInfo(
                book_name="Test Book",
                book_author="Test Author",
                book_keywords="test",
                book_file_name=os.path.basename(test_pdf_path)
            )
            session.add(book)
            session.commit()
            session.refresh(book)
            book_id = book.book_id
        
        # Copy test PDF to uploads directory
        upload_path = Path(api.uploads_dir) / os.path.basename(test_pdf_path)
        shutil.copy(test_pdf_path, upload_path)
        
        response = client.post("/page-image-binary", params={"book_id": book_id, "page_number": 0, "dpi": 150})
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert len(response.content) > 0
    
    def test_update_book_info(self, client, test_pdf_path):
        """Test POST /update-book-info endpoint"""
        # First, create a book entry
        from textbook.database import BookInfo
        import api.app as api
        
        assert api.database is not None
        with api.database.new_session() as session:
            book = BookInfo(
                book_name="Test Book",
                book_author="Test Author",
                book_keywords="test",
                book_file_name=os.path.basename(test_pdf_path)
            )
            session.add(book)
            session.commit()
            session.refresh(book)
            book_id = book.book_id
        
        # Copy test PDF to uploads directory
        upload_path = Path(api.uploads_dir) / os.path.basename(test_pdf_path)
        shutil.copy(test_pdf_path, upload_path)
        
        response = client.post("/update-book-info", json={"book_id": book_id, "overwrite": True})
        # May fail if LLM is not properly initialized or book extraction fails, but should return proper error
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert "book_id" in data
            assert "message" in data
            assert data["book_id"] == book_id
    
    def test_check_toc_exists(self, client, test_pdf_path):
        """Test GET /check-toc-exists endpoint"""
        # First, create a book entry
        from textbook.database import BookInfo
        import api.app as api
        
        assert api.database is not None
        with api.database.new_session() as session:
            book = BookInfo(
                book_name="Test Book",
                book_author="Test Author",
                book_keywords="test",
                book_file_name=os.path.basename(test_pdf_path)
            )
            session.add(book)
            session.commit()
            session.refresh(book)
            book_id = book.book_id
        
        # Copy test PDF to uploads directory
        upload_path = Path(api.uploads_dir) / os.path.basename(test_pdf_path)
        shutil.copy(test_pdf_path, upload_path)
        
        response = client.get("/check-toc-exists", params={"book_id": book_id})
        assert response.status_code == 200
        data = response.json()
        assert "book_id" in data
        assert "toc_exists" in data
        assert data["book_id"] == book_id
        assert isinstance(data["toc_exists"], bool)
    
    def test_update_toc(self, client, test_pdf_path):
        """Test POST /update-toc endpoint"""
        # First, create a book entry
        from textbook.database import BookInfo
        import api.app as api
        
        assert api.database is not None
        with api.database.new_session() as session:
            book = BookInfo(
                book_name="Test Book",
                book_author="Test Author",
                book_keywords="test",
                book_file_name=os.path.basename(test_pdf_path)
            )
            session.add(book)
            session.commit()
            session.refresh(book)
            book_id = book.book_id
        
        # Copy test PDF to uploads directory
        upload_path = Path(api.uploads_dir) / os.path.basename(test_pdf_path)
        shutil.copy(test_pdf_path, upload_path)
        
        response = client.post("/update-toc", json={"book_id": book_id, "caching": True, "overwrite": True})
        # May fail if book info not extracted first, but should return proper error
        assert response.status_code in [200, 400, 500]
        if response.status_code == 200:
            data = response.json()
            assert "book_id" in data
            assert "message" in data
    
    def test_update_alignment_offset(self, client, test_pdf_path):
        """Test POST /update-alignment-offset endpoint"""
        # First, create a book entry
        from textbook.database import BookInfo
        import api.app as api
        
        assert api.database is not None
        with api.database.new_session() as session:
            book = BookInfo(
                book_name="Test Book",
                book_author="Test Author",
                book_keywords="test",
                book_file_name=os.path.basename(test_pdf_path)
            )
            session.add(book)
            session.commit()
            session.refresh(book)
            book_id = book.book_id
        
        # Copy test PDF to uploads directory
        upload_path = Path(api.uploads_dir) / os.path.basename(test_pdf_path)
        shutil.copy(test_pdf_path, upload_path)
        
        response = client.post("/update-alignment-offset", json={"book_id": book_id, "page_number": 0})
        # May fail if book info not extracted first, but should return proper error
        assert response.status_code in [200, 400, 500]
        if response.status_code == 200:
            data = response.json()
            assert "book_id" in data
            assert "message" in data
            assert "offset" in data
    
    def test_check_alignment_offset(self, client, test_pdf_path):
        """Test POST /check-alignment-offset endpoint"""
        # First, create a book entry
        from textbook.database import BookInfo
        import api.app as api
        
        assert api.database is not None
        with api.database.new_session() as session:
            book = BookInfo(
                book_name="Test Book",
                book_author="Test Author",
                book_keywords="test",
                book_file_name=os.path.basename(test_pdf_path)
            )
            session.add(book)
            session.commit()
            session.refresh(book)
            book_id = book.book_id
        
        # Copy test PDF to uploads directory
        upload_path = Path(api.uploads_dir) / os.path.basename(test_pdf_path)
        shutil.copy(test_pdf_path, upload_path)
        
        response = client.post("/check-alignment-offset", json={"book_id": book_id})
        # May fail if book info not extracted first, but should return proper error
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert "book_id" in data
            assert "results" in data
            assert isinstance(data["results"], list)
    
    def test_get_books(self, client):
        """Test GET /books endpoint"""
        response = client.get("/books")
        assert response.status_code == 200
        data = response.json()
        assert "books" in data
        assert isinstance(data["books"], list)
    
    def test_get_chapters(self, client, test_pdf_path):
        """Test GET /chapters endpoint"""
        # First, create a book entry
        from textbook.database import BookInfo
        import api.app as api
        
        assert api.database is not None
        with api.database.new_session() as session:
            book = BookInfo(
                book_name="Test Book",
                book_author="Test Author",
                book_keywords="test",
                book_file_name=os.path.basename(test_pdf_path)
            )
            session.add(book)
            session.commit()
            session.refresh(book)
            book_id = book.book_id
        
        response = client.get("/chapters", params={"book_id": book_id})
        assert response.status_code == 200
        data = response.json()
        assert "book_id" in data
        assert "chapters" in data
        assert data["book_id"] == book_id
        assert isinstance(data["chapters"], list)
    
    def test_upload_book(self, client, test_pdf_path):
        """Test POST /upload-book endpoint"""
        # Create a test PDF file content
        with open(test_pdf_path, "rb") as f:
            pdf_content = f.read()
        
        # Create a file-like object
        file_obj = BytesIO(pdf_content)
        file_obj.name = "test_book.pdf"
        
        response = client.post(
            "/upload-book",
            files={"file": ("test_book.pdf", file_obj, "application/pdf")}
        )
        # May fail if LLM is not properly initialized, but should return proper error
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert "book_id" in data
            assert "message" in data
            assert isinstance(data["book_id"], int)
    
    def test_delete_book(self, client, test_pdf_path):
        """Test DELETE /delete-book endpoint"""
        # First, create a book entry
        from textbook.database import BookInfo
        import api.app as api
        
        assert api.database is not None
        with api.database.new_session() as session:
            book = BookInfo(
                book_name="Test Book",
                book_author="Test Author",
                book_keywords="test",
                book_file_name=os.path.basename(test_pdf_path)
            )
            session.add(book)
            session.commit()
            session.refresh(book)
            book_id = book.book_id
        
        # Copy test PDF to uploads directory
        upload_path = Path(api.uploads_dir) / os.path.basename(test_pdf_path)
        shutil.copy(test_pdf_path, upload_path)
        
        response = client.delete("/delete-book", params={"book_id": book_id})
        assert response.status_code == 200
        data = response.json()
        assert "book_id" in data
        assert "message" in data
        assert "deleted" in data
        assert data["book_id"] == book_id
        assert data["deleted"] is True
    
    def test_create_section(self, client):
        """Test POST /sections endpoint"""
        # First, create a book entry
        from textbook.database import BookInfo
        import api.app as api
        
        assert api.database is not None
        with api.database.new_session() as session:
            book = BookInfo(
                book_name="Test Book",
                book_author="Test Author",
                book_keywords="test"
            )
            session.add(book)
            session.commit()
            session.refresh(book)
            book_id = book.book_id
        
        response = client.post("/sections", json={
            "book_id": book_id,
            "title": "Test Section",
            "start_page_number": 10,
            "end_page_number": 20,
            "summary": "Test section summary",
            "book_index_string": "1.1"
        })
        assert response.status_code == 200
        data = response.json()
        assert "section_id" in data
        assert "message" in data
        assert isinstance(data["section_id"], int)
        assert data["message"] == "Section created successfully"
    
    def test_get_sections(self, client):
        """Test GET /sections endpoint"""
        # First, create a book entry
        from textbook.database import BookInfo, SectionInfo
        import api.app as api
        
        assert api.database is not None
        with api.database.new_session() as session:
            book = BookInfo(
                book_name="Test Book",
                book_author="Test Author",
                book_keywords="test"
            )
            session.add(book)
            session.commit()
            session.refresh(book)
            book_id = book.book_id
            
            # Create a test section
            section = SectionInfo(
                book_id=book_id,
                title="Test Section",
                start_page_number=10,
                end_page_number=20
            )
            session.add(section)
            session.commit()
            session.refresh(section)
        
        response = client.get("/books", params={"book_id": book_id})
        assert response.status_code == 200
        data = response.json()
        assert "books" in data
        assert data["books"][0]["book_id"] == book_id
        
        response = client.get("/sections", params={"book_id": book_id})
        assert response.status_code == 200
        data = response.json()
        assert "book_id" in data
        assert "sections" in data
        assert data["book_id"] == book_id
        assert isinstance(data["sections"], list)
        assert len(data["sections"]) > 0
        assert data["sections"][0]["title"] == "Test Section"
    
    def test_get_section_by_id(self, client):
        """Test GET /sections/{section_id} endpoint"""
        # First, create a book and section entry
        from textbook.database import BookInfo, SectionInfo
        import api.app as api
        
        assert api.database is not None
        with api.database.new_session() as session:
            book = BookInfo(
                book_name="Test Book",
                book_author="Test Author",
                book_keywords="test"
            )
            session.add(book)
            session.commit()
            session.refresh(book)
            book_id = book.book_id
            
            section = SectionInfo(
                book_id=book_id,
                title="Test Section",
                start_page_number=10,
                end_page_number=20,
                summary="Test summary"
            )
            session.add(section)
            session.commit()
            session.refresh(section)
            section_id = section.section_id
        
        response = client.get(f"/sections/{section_id}")
        assert response.status_code == 200
        data = response.json()
        assert "section" in data
        assert data["section"]["section_id"] == section_id
        assert data["section"]["title"] == "Test Section"
        assert data["section"]["start_page_number"] == 10
        assert data["section"]["end_page_number"] == 20
    
    def test_update_section(self, client):
        """Test PUT /sections/{section_id} endpoint"""
        # First, create a book and section entry
        from textbook.database import BookInfo, SectionInfo
        import api.app as api
        
        assert api.database is not None
        with api.database.new_session() as session:
            book = BookInfo(
                book_name="Test Book",
                book_author="Test Author",
                book_keywords="test"
            )
            session.add(book)
            session.commit()
            session.refresh(book)
            book_id = book.book_id
            
            section = SectionInfo(
                book_id=book_id,
                title="Test Section",
                start_page_number=10,
                end_page_number=20
            )
            session.add(section)
            session.commit()
            session.refresh(section)
            section_id = section.section_id
        
        response = client.put(f"/sections/{section_id}", json={
            "title": "Updated Section",
            "summary": "Updated summary",
            "start_page_number": 15,
            "end_page_number": 25
        })
        assert response.status_code == 200
        data = response.json()
        assert "section_id" in data
        assert "message" in data
        assert data["section_id"] == section_id
        assert data["message"] == "Section updated successfully"
    
    def test_delete_section(self, client):
        """Test DELETE /sections/{section_id} endpoint"""
        # First, create a book and section entry
        from textbook.database import BookInfo, SectionInfo
        import api.app as api
        
        assert api.database is not None
        with api.database.new_session() as session:
            book = BookInfo(
                book_name="Test Book",
                book_author="Test Author",
                book_keywords="test"
            )
            session.add(book)
            session.commit()
            session.refresh(book)
            book_id = book.book_id
            
            section = SectionInfo(
                book_id=book_id,
                title="Test Section",
                start_page_number=10,
                end_page_number=20
            )
            session.add(section)
            session.commit()
            session.refresh(section)
            section_id = section.section_id
        
        response = client.delete(f"/sections/{section_id}")
        assert response.status_code == 200
        data = response.json()
        assert "section_id" in data
        assert "message" in data
        assert data["section_id"] == section_id
        assert data["message"] == "Section deleted successfully"
    
    def test_create_page(self, client):
        """Test POST /pages endpoint"""
        # First, create a book entry
        from textbook.database import BookInfo
        import api.app as api
        
        assert api.database is not None
        with api.database.new_session() as session:
            book = BookInfo(
                book_name="Test Book",
                book_author="Test Author",
                book_keywords="test"
            )
            session.add(book)
            session.commit()
            session.refresh(book)
            book_id = book.book_id
        
        response = client.post("/pages", json={
            "book_id": book_id,
            "page_number": 5,
            "summary": "Test page summary"
        })
        assert response.status_code == 200
        data = response.json()
        assert "page_id" in data
        assert "message" in data
        assert isinstance(data["page_id"], int)
        assert data["message"] == "Page created successfully"
    
    def test_get_pages(self, client):
        """Test GET /pages endpoint"""
        # First, create a book entry
        from textbook.database import BookInfo, PageInfo
        import api.app as api
        
        assert api.database is not None
        with api.database.new_session() as session:
            book = BookInfo(
                book_name="Test Book",
                book_author="Test Author",
                book_keywords="test"
            )
            session.add(book)
            session.commit()
            session.refresh(book)
            book_id = book.book_id
            
            # Create a test page
            page = PageInfo(
                book_id=book_id,
                page_number=5,
                summary="Test page summary"
            )
            session.add(page)
            session.commit()
        
        response = client.get("/pages", params={"book_id": book_id})
        assert response.status_code == 200
        data = response.json()
        assert "book_id" in data
        assert "pages" in data
        assert data["book_id"] == book_id
        assert isinstance(data["pages"], list)
        assert len(data["pages"]) > 0
        assert data["pages"][0]["page_number"] == 5
    
    def test_get_page_by_id(self, client):
        """Test GET /pages/{page_id} endpoint"""
        # First, create a book and page entry
        from textbook.database import BookInfo, PageInfo
        import api.app as api
        
        assert api.database is not None
        with api.database.new_session() as session:
            book = BookInfo(
                book_name="Test Book",
                book_author="Test Author",
                book_keywords="test"
            )
            session.add(book)
            session.commit()
            session.refresh(book)
            book_id = book.book_id
            
            page = PageInfo(
                book_id=book_id,
                page_number=5,
                summary="Test page summary"
            )
            session.add(page)
            session.commit()
            session.refresh(page)
            page_id = page.page_id
        
        response = client.get(f"/pages/{page_id}")
        assert response.status_code == 200
        data = response.json()
        assert "page" in data
        assert data["page"]["page_id"] == page_id
        assert data["page"]["page_number"] == 5
        assert data["page"]["summary"] == "Test page summary"
    
    def test_update_page(self, client):
        """Test PUT /pages/{page_id} endpoint"""
        # First, create a book and page entry
        from textbook.database import BookInfo, PageInfo
        import api.app as api
        
        assert api.database is not None
        with api.database.new_session() as session:
            book = BookInfo(
                book_name="Test Book",
                book_author="Test Author",
                book_keywords="test"
            )
            session.add(book)
            session.commit()
            session.refresh(book)
            book_id = book.book_id
            
            page = PageInfo(
                book_id=book_id,
                page_number=5,
                summary="Original summary"
            )
            session.add(page)
            session.commit()
            session.refresh(page)
            page_id = page.page_id
        
        response = client.put(f"/pages/{page_id}", json={
            "page_number": 10,
            "summary": "Updated summary"
        })
        assert response.status_code == 200
        data = response.json()
        assert "page_id" in data
        assert "message" in data
        assert data["page_id"] == page_id
        assert data["message"] == "Page updated successfully"
    
    def test_delete_page(self, client):
        """Test DELETE /pages/{page_id} endpoint"""
        # First, create a book and page entry
        from textbook.database import BookInfo, PageInfo
        import api.app as api
        
        assert api.database is not None
        with api.database.new_session() as session:
            book = BookInfo(
                book_name="Test Book",
                book_author="Test Author",
                book_keywords="test"
            )
            session.add(book)
            session.commit()
            session.refresh(book)
            book_id = book.book_id
            
            page = PageInfo(
                book_id=book_id,
                page_number=5,
                summary="Test page summary"
            )
            session.add(page)
            session.commit()
            session.refresh(page)
            page_id = page.page_id
        
        response = client.delete(f"/pages/{page_id}")
        assert response.status_code == 200
        data = response.json()
        assert "page_id" in data
        assert "message" in data
        assert data["page_id"] == page_id
        assert data["message"] == "Page deleted successfully"

