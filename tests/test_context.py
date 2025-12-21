"""
Unit tests for TextBookContext class
"""
import os
# Set dummy API key to avoid import errors (tests don't use LLM)
os.environ.setdefault("LLM_GEMINI_KEY", "dummy_key_for_testing")

import pytest
import tempfile
from textbook.context import (
    TextBookContext,
    BookInfo,
    ChapterInfo,
    SectionInfo,
    PageInfo,
    ExerciseInfo,
    ExerciseDetails,
)


class TestTextBookContext:
    """Test suite for TextBookContext class"""
    
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
    def context(self, temp_db):
        """Create a TextBookContext instance with temporary database"""
        ctx = TextBookContext(db_path=temp_db)
        yield ctx
        ctx.close()
    
    def test_init_default_path(self):
        """Test initialization with default database path"""
        ctx = TextBookContext()
        assert ctx.db_path == "textbook_context.db"
        assert ctx.db_type == "sqlite"
        assert ctx.engine is not None
        ctx.close()
        # Cleanup
        if os.path.exists("textbook_context.db"):
            os.unlink("textbook_context.db")
    
    def test_init_custom_path(self, temp_db):
        """Test initialization with custom database path"""
        ctx = TextBookContext(db_path=temp_db)
        assert ctx.db_path == temp_db
        assert ctx.engine is not None
        ctx.close()
    
    def test_init_custom_directory(self):
        """Test initialization with custom directory path"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "subdir", "test.db")
            ctx = TextBookContext(db_path=db_path)
            assert os.path.exists(db_path)
            assert ctx.engine is not None
            ctx.close()
    
    def test_init_invalid_db_type(self):
        """Test initialization with invalid database type"""
        with pytest.raises(ValueError, match="Unsupported database type"):
            TextBookContext(db_type="invalid")
    
    def test_init_postgresql_not_implemented(self):
        """Test that PostgreSQL raises NotImplementedError"""
        with pytest.raises(NotImplementedError, match="PostgreSQL support"):
            TextBookContext(db_type="postgresql")
    
    def test_tables_created(self, context):
        """Test that all tables are created"""
        from sqlalchemy import inspect
        
        inspector = inspect(context.engine)
        tables = inspector.get_table_names()
        
        assert "book_info" in tables
        assert "chapter_info" in tables
        assert "section_info" in tables
        assert "page_info" in tables
        assert "exercise_info" in tables
        assert "exercise_details" in tables
    
    def test_context_manager(self, temp_db):
        """Test context manager functionality"""
        with TextBookContext(db_path=temp_db) as ctx:
            assert ctx.engine is not None
            assert ctx.session is not None
        
        # Session should be closed after context exit
        assert ctx._session is None
    
    def test_close(self, context):
        """Test closing the database connection"""
        assert context.session is not None
        context.close()
        assert context._session is None
    
    def test_create_book(self, context):
        """Test creating a book"""
        embedding = b'\x01\x02\x03\x04\x05' * 200
        book = BookInfo(
            book_name="Test Book",
            book_author="Test Author",
            book_pages=500,
            book_keywords="mathematics, algebra",
            book_summary="A test book for mathematics",
            book_embedding=embedding,
        )
        context.session.add(book)
        context.session.commit()
        
        # Check auto-increment worked
        assert book.book_id == 1
        
        retrieved = context.session.get(BookInfo, 1)
        assert retrieved is not None
        assert retrieved.book_id == 1
        assert retrieved.book_name == "Test Book"
        assert retrieved.book_author == "Test Author"
        assert retrieved.book_pages == 500
        assert retrieved.book_keywords == "mathematics, algebra"
        assert retrieved.book_summary == "A test book for mathematics"
        assert retrieved.book_embedding == embedding
    
    def test_create_book_auto_increment(self, context):
        """Test that book_id auto-increments correctly"""
        book1 = BookInfo(book_name="Book 1")
        book2 = BookInfo(book_name="Book 2")
        context.session.add_all([book1, book2])
        context.session.commit()
        
        assert book1.book_id == 1
        assert book2.book_id == 2
        
        retrieved1 = context.session.get(BookInfo, 1)
        retrieved2 = context.session.get(BookInfo, 2)
        assert retrieved1.book_name == "Book 1"
        assert retrieved2.book_name == "Book 2"
    
    def test_create_book_nullable_fields(self, context):
        """Test that book fields can be None"""
        book = BookInfo()
        context.session.add(book)
        context.session.commit()
        
        assert book.book_id == 1
        retrieved = context.session.get(BookInfo, 1)
        assert retrieved.book_name is None
        assert retrieved.book_author is None
        assert retrieved.book_pages is None
        assert retrieved.book_keywords is None
        assert retrieved.book_summary is None
        assert retrieved.book_embedding is None
    
    def test_create_chapter(self, context):
        """Test creating a chapter"""
        chapter = ChapterInfo(
            chapter_id=1,
            start_page_number=1,
            end_page_number=20,
            summary="Introduction chapter",
            book_index_string="1.2.3"
        )
        context.session.add(chapter)
        context.session.commit()
        
        retrieved = context.session.get(ChapterInfo, 1)
        assert retrieved is not None
        assert retrieved.chapter_id == 1
        assert retrieved.start_page_number == 1
        assert retrieved.end_page_number == 20
        assert retrieved.summary == "Introduction chapter"
        assert retrieved.book_index_string == "1.2.3"
    
    def test_create_section(self, context):
        """Test creating a section"""
        section = SectionInfo(
            section_id=1,
            start_page_number=1,
            end_page_number=10,
            summary="First section",
            chapter_id=1,
            book_index_string="1.2.3"
        )
        context.session.add(section)
        context.session.commit()
        
        retrieved = context.session.get(SectionInfo, 1)
        assert retrieved is not None
        assert retrieved.section_id == 1
        assert retrieved.chapter_id == 1
        assert retrieved.book_index_string == "1.2.3"
    
    def test_create_page(self, context):
        """Test creating a page"""
        embedding = b'\x01\x02\x03\x04\x05' * 100
        page = PageInfo(
            page_number=1,
            summary="First page summary",
            embedding=embedding,
            related_chapters=b'ch1',
            related_section_id=b'sec1'
        )
        context.session.add(page)
        context.session.commit()
        
        retrieved = context.session.get(PageInfo, 1)
        assert retrieved is not None
        assert retrieved.page_number == 1
        assert retrieved.summary == "First page summary"
        assert retrieved.embedding == embedding
        assert retrieved.related_chapters == b'ch1'
        assert retrieved.related_section_id == b'sec1'
    
    def test_create_exercise_info(self, context):
        """Test creating exercise info"""
        # First create a page (required for foreign key)
        page = PageInfo(page_number=5, summary="Test page")
        context.session.add(page)
        context.session.commit()
        
        exercise = ExerciseInfo(
            exercise_id=1,
            exercise_description="Solve problem 1",
            page_number=5,
            page_id=1,
            embedding=b'\x01\x02\x03',
            related_chapters=b'ch1',
            related_section_id=b'sec1'
        )
        context.session.add(exercise)
        context.session.commit()
        
        retrieved = context.session.get(ExerciseInfo, 1)
        assert retrieved is not None
        assert retrieved.exercise_id == 1
        assert retrieved.exercise_description == "Solve problem 1"
        assert retrieved.page_number == 5
    
    def test_create_exercise_details(self, context):
        """Test creating exercise details"""
        # First create page and exercise info
        page = PageInfo(page_number=5, summary="Test page")
        context.session.add(page)
        exercise_info = ExerciseInfo(
            exercise_id=1,
            exercise_description="Solve problem 1",
            page_number=5,
            page_id=1,
        )
        context.session.add(exercise_info)
        context.session.commit()
        
        details = ExerciseDetails(
            exercise_id=1,
            study_guide="Review chapter 1",
            estimated_time_to_complete=30,
            difficulty_level=2
        )
        context.session.add(details)
        context.session.commit()
        
        retrieved = context.session.get(ExerciseDetails, 1)
        assert retrieved is not None
        assert retrieved.exercise_id == 1
        assert retrieved.study_guide == "Review chapter 1"
        assert retrieved.estimated_time_to_complete == 30
        assert retrieved.difficulty_level == 2
    
    def test_chapter_section_relationship(self, context):
        """Test relationship between chapter and sections"""
        chapter = ChapterInfo(
            chapter_id=1,
            start_page_number=1,
            end_page_number=20
        )
        section1 = SectionInfo(
            section_id=1,
            start_page_number=1,
            end_page_number=10,
            chapter_id=1
        )
        section2 = SectionInfo(
            section_id=2,
            start_page_number=11,
            end_page_number=20,
            chapter_id=1
        )
        
        context.session.add_all([chapter, section1, section2])
        context.session.commit()
        
        # Test relationship
        retrieved_chapter = context.session.get(ChapterInfo, 1)
        assert len(retrieved_chapter.sections) == 2
        assert retrieved_chapter.sections[0].section_id == 1
        assert retrieved_chapter.sections[1].section_id == 2
    
    def test_page_exercise_relationship(self, context):
        """Test relationship between page and exercises"""
        page = PageInfo(page_id=1, page_number=5, summary="Test page")
        exercise1 = ExerciseInfo(
            exercise_id=1,
            exercise_description="Exercise 1",
            page_number=5,
            page_id=1
        )
        exercise2 = ExerciseInfo(
            exercise_id=2,
            exercise_description="Exercise 2",
            page_number=5,
            page_id=1
        )
        
        context.session.add_all([page, exercise1, exercise2])
        context.session.commit()
        
        # Test relationship
        retrieved_page = context.session.get(PageInfo, 1)
        assert len(retrieved_page.exercises) == 2
        assert retrieved_page.exercises[0].exercise_id == 1
        assert retrieved_page.exercises[1].exercise_id == 2
    
    def test_exercise_info_details_relationship(self, context):
        """Test relationship between exercise info and details"""
        page = PageInfo(page_number=5, summary="Test page")
        exercise_info = ExerciseInfo(
            exercise_id=1,
            exercise_description="Exercise 1",
            page_number=5,
            page_id=1
        )
        exercise_details = ExerciseDetails(
            exercise_id=1,
            study_guide="Study guide",
            estimated_time_to_complete=30,
            difficulty_level=2
        )
        
        context.session.add_all([page, exercise_info, exercise_details])
        context.session.commit()
        
        # Test relationship
        retrieved_info = context.session.get(ExerciseInfo, 1)
        assert retrieved_info.details is not None
        assert retrieved_info.details.study_guide == "Study guide"
        assert retrieved_info.details.difficulty_level == 2
    
    def test_nullable_fields(self, context):
        """Test that nullable fields can be None"""
        chapter = ChapterInfo(
            chapter_id=1,
            start_page_number=1,
            end_page_number=None,
            summary=None
        )
        context.session.add(chapter)
        context.session.commit()
        
        retrieved = context.session.get(ChapterInfo, 1)
        assert retrieved.end_page_number is None
        assert retrieved.summary is None