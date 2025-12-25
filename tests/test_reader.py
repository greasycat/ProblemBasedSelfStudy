import os
import pytest
import shutil
from pathlib import Path

# Set dummy API key to avoid import errors (tests don't use LLM for actual calls)
# os.environ.setdefault("LLM_GEMINI_KEY", "dummy_key_for_testing")

from textbook.reader import LazyTextbookReader
from textbook.database import TextBookDatabase
from textbook.model import LLM

scan_book_path = Path("tests/textbooks/topology_scan.pdf")
database_path = "tests/databases/toc_only.db"


class TestLazyTextbookReader:
    """Test suite for LazyTextbookReader class"""
    
    @pytest.fixture
    def database(self):
        """Create a TextBookContext instance with temporary database by copying the toc_only.db file"""
        if not os.path.exists(database_path):
            raise FileNotFoundError(f"Test Database file not found: {database_path}")
        shutil.copy(database_path, "tests/databases/toc_only_copy.db")
        database = TextBookDatabase(db_path="tests/databases/toc_only_copy.db")
        yield database
        database.close()
        if os.path.exists("tests/databases/toc_only_copy.db"):
            os.unlink("tests/databases/toc_only_copy.db")

    @pytest.fixture
    def llm(self):
        """Create an LLM instance"""
        # Note: This will use dummy key, actual LLM calls may fail but we use force_text_only_extraction
        try:
            return LLM()
        except Exception:
            # If LLM initialization fails, we'll skip the test
            pytest.skip("LLM initialization failed (expected with dummy key)")
    
    def test_get_page_30_contains_text(self, database: TextBookDatabase, llm: LLM):
        """Test that page 30 from scan PDF contains 'the concept of function'"""
        if not scan_book_path.exists():
            pytest.skip(f"Test PDF file not found: {scan_book_path}")
        
        # Use force_text_only_extraction to avoid needing MinerU
        with LazyTextbookReader(scan_book_path, llm, database, force_text_only_extraction=False) as reader:
            # Page numbers are 0-indexed, so page 30 (1-indexed) is page 29 (0-indexed)
            page_text = reader.get_page_content(29)

            print("page_text: ", page_text)
            
            # Check that the text contains "the concept of function" (case-insensitive)
            assert "the concept of function" in page_text.lower(), \
                f"Page 30 should contain 'the concept of function', but got: {page_text[:200]}..."
            
            page_id = reader.create_or_update_page_info(29)

            assert page_id is not None, "Failed to create page"

            page = database.get_page_info(page_id)
            assert page is not None, "Failed to get page"

            print("page: ", page.summary)

        