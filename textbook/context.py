# The TextBookContext class is used to read/write the context of a textbook to database
# Currently implemented with SQLite3, with room for PostgreSQL implementation later
# The following tables are used to store the context of the textbook:
# book_info: table of book information, a table with columns: book_id (auto-increment), book_name (str), book_author (str),  book_pages (int), book_keywords (str), book_summary (str), book_embedding (BLOB),
# chapter_info: table of chapter summaries, a table with columns: chapter_id (auto-increment), start_page_number (int), end_page_number, summary, book_id, book_index_string (str)
# section_info: table of sections, a table with columns: section_id (auto-increment), start_page_number (int), end_page_number (int), summary, chapter_id, book_id, book_index_string (str)
# page_info: table of page summaries, a table with columns: page_id (auto-increment), page_number (not auto-increment), summary, embedding (BLOB), related_chapters (BLOB), related_section_id (BLOB), book_id
# exercise_info: table of exercise information, a table with columns: exercise_id (not auto-increment), exercise_description, page_number (int), related_chapters (BLOB), related_section_id (BLOB), embedding (BLOB), book_id
# exercise_details: table of exercise details, a table with columns: exercise_id (not auto-increment), study_guide (str), estimated_time_to_complete (int), difficulty_level (int), chapter_id, section_id, book_id 

import os
from pathlib import Path
from typing import Optional
from sqlalchemy import (
    create_engine,
    String,
    Integer,
    Text,
    LargeBinary,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    Session,
)
from sqlalchemy.engine import Engine


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""
    pass


class BookInfo(Base):
    """Model for book information"""
    __tablename__ = "book_info"
    
    book_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    book_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    book_author: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    book_pages: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    book_keywords: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    book_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    book_embedding: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    book_file_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Relationships to other tables
    chapters: Mapped[list["ChapterInfo"]] = relationship(
        "ChapterInfo",
        back_populates="book",
        cascade="all, delete-orphan"
    )
    sections: Mapped[list["SectionInfo"]] = relationship(
        "SectionInfo",
        back_populates="book",
        cascade="all, delete-orphan"
    )
    pages: Mapped[list["PageInfo"]] = relationship(
        "PageInfo",
        back_populates="book",
        cascade="all, delete-orphan"
    )
    exercises: Mapped[list["ExerciseInfo"]] = relationship(
        "ExerciseInfo",
        back_populates="book",
        cascade="all, delete-orphan"
    )


class ChapterInfo(Base):
    """Model for chapter information
    
    Args:
        chapter_id: The ID of the chapter
        start_page_number: The page number of the first page of the chapter
        end_page_number: The page number of the last page of the chapter
        summary: The summary of the chapter
        book_index_string: The index string of the chapter
        book_id: The ID of the book
    """
    
    __tablename__ = "chapter_info"
    
    chapter_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    start_page_number: Mapped[int] = mapped_column(Integer)
    end_page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    book_index_string: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    book_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("book_info.book_id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Relationship to book
    book: Mapped[Optional["BookInfo"]] = relationship(
        "BookInfo",
        back_populates="chapters"
    )
    
    # Relationship to sections
    sections: Mapped[list["SectionInfo"]] = relationship(
        "SectionInfo",
        back_populates="chapter",
        cascade="all, delete-orphan"
    )
    
    # Indexes for common queries
    __table_args__ = (
        UniqueConstraint("book_id", "chapter_id", name="uq_chapter_info_book_id_chapter_id"),
        UniqueConstraint("book_id", "title", name="uq_chapter_info_book_id_title"),
        Index("idx_chapter_info_book_id", "book_id"),
    )


class SectionInfo(Base):
    """Model for section information
    Args:
        section_id: The ID of the section
        start_page_number: The page number of the first page of the section
        end_page_number: The page number of the last page of the section
        summary: The summary of the section
        chapter_id: The ID of the chapter
        book_index_string: The index string of the section
        book_id: The ID of the book
    """
    __tablename__ = "section_info"
    
    section_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    start_page_number: Mapped[int] = mapped_column(Integer)
    end_page_number: Mapped[int] = mapped_column(Integer)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    chapter_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("chapter_info.chapter_id", ondelete="SET NULL"),
    )
    book_index_string: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    book_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("book_info.book_id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Relationship to book
    book: Mapped[Optional["BookInfo"]] = relationship(
        "BookInfo",
        back_populates="sections"
    )
    
    # Relationship to chapter
    chapter: Mapped[Optional["ChapterInfo"]] = relationship(
        "ChapterInfo",
        back_populates="sections"
    )
    
    # Indexes for common queries
    __table_args__ = (
        UniqueConstraint("book_id", "section_id", name="uq_section_info_book_id_section_id"),
        UniqueConstraint("book_id", "title", name="uq_section_info_book_id_title"),
        Index("idx_section_info_chapter_id", "chapter_id"),
        Index("idx_section_info_book_id", "book_id"),
        Index("idx_section_info_start_page", "start_page_number"),
    )


class PageInfo(Base):
    """Model for page information"""
    __tablename__ = "page_info"
    
    page_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    embedding: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    related_chapters: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    related_section_id: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    book_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("book_info.book_id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Relationship to book
    book: Mapped[Optional["BookInfo"]] = relationship(
        "BookInfo",
        back_populates="pages"
    )
    
    # Relationship to exercises
    exercises: Mapped[list["ExerciseInfo"]] = relationship(
        "ExerciseInfo",
        back_populates="page",
        cascade="all, delete-orphan"
    )
    
    # Indexes for common queries
    __table_args__ = (
        UniqueConstraint("book_id", "page_id", name="uq_page_info_book_id_page_id"),
        UniqueConstraint("book_id", "page_number", name="uq_page_info_book_id_page_number"),
        Index("idx_page_info_book_id", "book_id"),
    )


class ExerciseInfo(Base):
    """Model for exercise information"""
    __tablename__ = "exercise_info"
    
    exercise_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    exercise_description: Mapped[str] = mapped_column(Text, nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    page_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("page_info.page_id", ondelete="CASCADE"),
        nullable=True,
    )
    related_chapters: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    related_section_id: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    embedding: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    book_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("book_info.book_id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Relationship to book
    book: Mapped[Optional["BookInfo"]] = relationship(
        "BookInfo",
        back_populates="exercises"
    )
    
    # Relationship to page
    page: Mapped["PageInfo"] = relationship("PageInfo", back_populates="exercises")
    
    # One-to-one relationship to exercise details
    details: Mapped[Optional["ExerciseDetails"]] = relationship(
        "ExerciseDetails",
        back_populates="exercise",
        cascade="all, delete-orphan",
        uselist=False
    )
    
    # Indexes for common queries
    __table_args__ = (
        UniqueConstraint("book_id", "exercise_id", name="uq_exercise_info_book_id_exercise_id"),
        Index("idx_exercise_info_page_number", "page_number"),
        Index("idx_exercise_info_book_id", "book_id"),
    )


class ExerciseDetails(Base):
    """Model for exercise details"""
    __tablename__ = "exercise_details"
    
    exercise_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("exercise_info.exercise_id", ondelete="CASCADE"),
        primary_key=True
    )
    study_guide: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    estimated_time_to_complete: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    difficulty_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    chapter_id: Mapped[Optional[str]] = mapped_column(
        String,
        ForeignKey("chapter_info.chapter_id", ondelete="SET NULL"),
        nullable=True
    )
    section_id: Mapped[Optional[str]] = mapped_column(
        String,
        ForeignKey("section_info.section_id", ondelete="SET NULL"),
        nullable=True
    )
    book_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("book_info.book_id", ondelete="CASCADE"),
        nullable=True
    )
    
    # Relationship to exercise info
    exercise: Mapped["ExerciseInfo"] = relationship(
        "ExerciseInfo",
        back_populates="details"
    )
    
    # Relationships to chapter and section
    chapter: Mapped[Optional["ChapterInfo"]] = relationship("ChapterInfo")
    section: Mapped[Optional["SectionInfo"]] = relationship("SectionInfo")
    book: Mapped[Optional["BookInfo"]] = relationship("BookInfo")
    
    # Indexes for common queries
    __table_args__ = (
        Index("idx_exercise_details_chapter_id", "chapter_id"),
        Index("idx_exercise_details_section_id", "section_id"),
        Index("idx_exercise_details_book_id", "book_id"),
    )


class TextBookContext:
    """Context manager for textbook database operations"""
    
    def __init__(
        self,
        db_path: Optional[str] = None,
        db_type: str = "sqlite"
    ):
        """
        Initialize TextBookContext
        
        Args:
            db_path: Path to the database file (for SQLite) or connection string
            db_type: Type of database ("sqlite" or "postgresql")
        """
        if db_type not in ("sqlite", "postgresql"):
            raise ValueError(f"Unsupported database type: {db_type}")
        
        if db_type == "postgresql":
            raise NotImplementedError("PostgreSQL support is not yet implemented")
        
        if db_path is None:
            db_path = "textbook_context.db"
        
        # Ensure directory exists
        db_dir = os.path.dirname(db_path)
        if db_dir:
            Path(db_dir).mkdir(parents=True, exist_ok=True)
        
        # Create SQLite connection string
        db_url = f"sqlite:///{db_path}"
        
        self.db_path = db_path
        self.db_type = db_type
        self.engine: Engine = create_engine(db_url, echo=False)
        
        # Create all tables
        Base.metadata.create_all(self.engine)
        
        # Create session (will be created per operation or can be used as context manager)
        self._session: Optional[Session] = None
    
    @property
    def session(self) -> Session:
        """Get or create a database session (lazy creation)"""
        if self._session is None:
            self._session = Session(self.engine)
        return self._session
    
    def new_session(self) -> Session:
        """
        Create a new database session
        
        Returns:
            A new Session instance. Caller is responsible for closing it.
        """
        return Session(self.engine)
    
    def close(self):
        """Close the database session"""
        if self._session:
            self._session.close()
            self._session = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    # Compatibility property for tests that access conn directly
    @property
    def conn(self):
        """Compatibility property for backward compatibility with raw SQLite connection"""
        # Return None to indicate SQLAlchemy is being used instead of raw connection
        return None