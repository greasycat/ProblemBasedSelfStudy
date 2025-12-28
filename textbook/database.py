# The TextBookContext class is used to read/write the context of a textbook to database
# Currently implemented with SQLite3, with room for PostgreSQL implementation later
# The following tables are used to store the context of the textbook:
# book_info: table of book information, a table with columns: book_id (auto-increment), book_name (str), book_author (str),  book_pages (int), book_keywords (str), book_summary (str), book_embedding (BLOB),
# chapter_info: table of chapter summaries, a table with columns: chapter_id (auto-increment), start_page_number (int), end_page_number, summary, book_id, book_index_string (str)
# section_info: table of sections, a table with columns: section_id (auto-increment), start_page_number (int), end_page_number (int), summary, chapter_id, book_id, book_index_string (str)
# page_info: table of page summaries, a table with columns: page_id (auto-increment), page_number (not auto-increment), summary, embedding (BLOB), related_chapters (BLOB), related_sections (BLOB), book_id
# exercise_info: table of exercise information, a table with columns: exercise_id (not auto-increment), exercise_description, page_number (int), related_chapters (BLOB), related_sections (BLOB), embedding (BLOB), book_id
# exercise_details: table of exercise details, a table with columns: exercise_id (not auto-increment), study_guide (str), estimated_time_to_complete (int), difficulty_level (int), chapter_id, section_id, book_id 

import os
from pathlib import Path
from typing import Optional, List
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
from sqlalchemy.exc import IntegrityError


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
    book_toc_end_page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    book_alignment_offset: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
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

    def __repr__(self) -> str:
        return f"BookInfo(book_id={self.book_id}, book_name={self.book_name}, book_author={self.book_author}, book_pages={self.book_pages}, book_keywords={self.book_keywords}, book_summary={self.book_summary}, book_embedding={self.book_embedding}, book_file_name={self.book_file_name}, book_toc_end_page={self.book_toc_end_page}, book_alignment_offset={self.book_alignment_offset})"
    
    def __str__(self) -> str:
        return self.__repr__()


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
    book_id: Mapped[int] = mapped_column(
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
    book_id: Mapped[int] = mapped_column(
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
    related_sections: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    book_id: Mapped[int] = mapped_column(
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
    related_sections: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    embedding: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    book_id: Mapped[int] = mapped_column(
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
    chapter_id: Mapped[Optional[int]] = mapped_column(
        String,
        ForeignKey("chapter_info.chapter_id", ondelete="SET NULL"),
        nullable=True
    )
    section_id: Mapped[Optional[str]] = mapped_column(
        String,
        ForeignKey("section_info.section_id", ondelete="SET NULL"),
        nullable=True
    )
    book_id: Mapped[int] = mapped_column(
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


class TextBookDatabase:
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

    

    
    # ------------------------------------------------------------
    # Book related functions
    # ------------------------------------------------------------

    def get_all_books(self) -> list[BookInfo]:
        """Get all books from the database"""
        with self.new_session() as session:
            return _query_all_books(session)

    def get_book_by_file_name(self, book_file_name: str) -> Optional[BookInfo]:
        with self.new_session() as session:
            return _query_book_by_file_name(session, book_file_name)

    def create_book(self, book_name: str, book_author: str, book_keywords: str, book_file_name: str, page_count: int) -> BookInfo:
        with self.new_session() as session:
            book_info = _create_book_and_return_info(session, book_name, book_author, book_keywords, book_file_name, page_count)
            if book_info is None:
                raise ValueError("Failed to create book")
            return book_info
    
    def get_book_toc_end_page(self, book_id: int, default_value: int) -> int:
        with self.new_session() as session:
            book_info = _query_book_by_id(session, book_id)
            if book_info is not None and book_info.book_toc_end_page is not None:
                return book_info.book_toc_end_page
            return default_value
        
    def update_book_toc_end_page(self, book_id: int, toc_end_page: int) -> None:
        with self.new_session() as session:
            session.query(BookInfo).filter(BookInfo.book_id == book_id).update({BookInfo.book_toc_end_page: toc_end_page})
            session.commit()
    
    def get_book_alignment_offset(self, book_id: int, default_value: int) -> int:
        with self.new_session() as session:
            book_info = _query_book_by_id(session, book_id)
            if book_info is not None and book_info.book_alignment_offset is not None:
                return book_info.book_alignment_offset
            return default_value
        
    def update_book_alignment_offset(self, book_id: int, alignment_offset: int) -> None:
        with self.new_session() as session:
            session.query(BookInfo).filter(BookInfo.book_id == book_id).update({BookInfo.book_alignment_offset: alignment_offset})
            session.commit()
        
    def delete_book_by_file_name(self, book_file_name: str) -> bool:
        with self.new_session() as session:
            book = _query_book_by_file_name(session, book_file_name)
            if book is None:
                return False
            
            session.delete(book)
            session.commit()
            return True
    # ------------------------------------------------------------
    # TOC related functions
    # ------------------------------------------------------------

    def delete_toc_by_book_id(self, book_id: int) -> None:
        with self.new_session() as session:
            _delete_sections_by_book_id(session, book_id)
            _delete_chapters_by_book_id(session, book_id)
            session.commit()
    
    # ------------------------------------------------------------
    # Chapter related functions
    # ------------------------------------------------------------

    def try_create_chapter_info(self, book_id: int, title: str, index_string: str, start_page: int, end_page: int) -> Optional[int]:
        with self.new_session() as session:
            existing = _query_chapter_by_book_id_and_title(session, book_id, title)
            if existing:
                return existing.chapter_id
            
            chapter_info = ChapterInfo(
                title=title,
                book_index_string=index_string,
                start_page_number=start_page,
                end_page_number=end_page,
                book_id=book_id
            )
            return _try_save(session, chapter_info)
    
    def get_chapters_by_book_id(self, book_id: int) -> list[ChapterInfo]:
        with self.new_session() as session:
            return _query_chapters_by_book_id(session, book_id)
        
    def get_chapters_by_book_id_and_page_range(self, book_id: int, start_page_number: int, end_page_number: int) -> List[ChapterInfo]:
        with self.new_session() as session:
            return _query_chapters_by_book_id_and_page_range(session, book_id, start_page_number, end_page_number)
    
    # ------------------------------------------------------------
    # Section related functions
    # ------------------------------------------------------------

    def try_create_section_info(self, book_id: int, chapter_id: int, title: str, index_string: str, start_page: int, end_page: int) -> Optional[int]:
        with self.new_session() as session:
            existing = _query_section_by_book_id_and_title(session, book_id, title)
            if existing:
                return existing.section_id
            
            section_info = SectionInfo(
                title=title,
                book_index_string=index_string,
                start_page_number=start_page,
                end_page_number=end_page,
                chapter_id=chapter_id,
                book_id=book_id
            )
            return _try_save(session, section_info)
        
    def get_sections_by_book_id(self, book_id: int) -> list[SectionInfo]:
        with self.new_session() as session:
            return _query_sections_by_book_id(session, book_id)

    def get_sections_by_book_id_and_page_range(self, book_id: int, start_page_number: int, end_page_number: int) -> List[SectionInfo]:
        with self.new_session() as session:
            return _query_sections_by_book_id_and_page_range(session, book_id, start_page_number, end_page_number)

    # ------------------------------------------------------------
    # Page related functions
    # ------------------------------------------------------------

    def try_create_page_info(self, book_id: int, page_number: int, summary: str) -> Optional[int]:
        with self.new_session() as session:
            existing = _query_page_by_book_id_and_page_number(session, book_id, page_number)
            if existing:
                return existing.page_id
            page_info = PageInfo(
                page_number=page_number,
                summary=summary,
                book_id=book_id
            )
            return _try_save(session, page_info)

    def get_page_info(self, page_id: int) -> Optional[PageInfo]:
        with self.new_session() as session:
            return _query_page_by_id(session, page_id)

def _try_save(session: Session, obj: Base):
    return_field = None
    if isinstance(obj, ChapterInfo):
        return_field = "chapter_id"
    elif isinstance(obj, SectionInfo):
        return_field = "section_id"
    elif isinstance(obj, PageInfo):
        return_field = "page_id"
    elif isinstance(obj, ExerciseInfo) or isinstance(obj, ExerciseDetails):
        return_field = "exercise_id"
    else:
        raise ValueError(f"Unsupported object type: {type(obj)}")
    
    try:
        session.add(obj)
        session.commit()
        session.flush()  # Flush to get auto-increment ID
        obj_id = getattr(obj, return_field, None)
        return obj_id
    except IntegrityError:
        print(f" {return_field} already exists, skipping")
        session.rollback()
        if isinstance(obj, ChapterInfo):
            if obj.end_page_number is None:
                raise ValueError("End page number is required for chapter")
            existing = _query_chapter_by_book_id_and_exact_page_range(session, obj.book_id, obj.start_page_number, obj.end_page_number)
            return existing.chapter_id if existing else None
        elif isinstance(obj, SectionInfo):
            if obj.end_page_number is None:
                raise ValueError("End page number is required for section")
            existing = _query_section_by_book_id_and_exact_page_range(session, obj.book_id, obj.start_page_number, obj.end_page_number)
            return existing.section_id if existing else None
        elif isinstance(obj, PageInfo):
            existing = _query_page_by_book_id_and_page_number(session, obj.book_id, obj.page_number)
            return existing.page_id if existing else None


    except Exception as e:
        print(f"Error adding {return_field}: {e}")
        session.rollback()
        return None
    
# ------------------------------------------------------------
# Book related functions
# ------------------------------------------------------------

def _query_book_by_id(session: Session, book_id: int) -> Optional[BookInfo]:
    """Query book by ID"""
    return session.query(BookInfo).filter(BookInfo.book_id == book_id).first()

def _query_book_by_file_name(session: Session, file_name: str) -> Optional[BookInfo]:
    """Query book by file name"""
    return session.query(BookInfo).filter(BookInfo.book_file_name == file_name).first()

def _query_all_books(session: Session) -> list[BookInfo]:
    """Query all books"""
    return session.query(BookInfo).all()

def _create_book_and_return_info(session: Session, book_name: str, book_author: str, book_keywords: str, book_file_name: str, page_count: int) -> Optional[BookInfo]:
        book_info = BookInfo(
            book_name=book_name,
            book_author=book_author,
            book_keywords=book_keywords,
            book_file_name=book_file_name,
            book_pages=page_count,
        )
        session.add(book_info)
        session.commit()
        session.refresh(book_info)
        return book_info

# ------------------------------------------------------------
# Chapter related functions
# ------------------------------------------------------------

def _query_chapters_by_book_id(session: Session, book_id: int) -> list[ChapterInfo]:
    """Query chapters by book ID"""
    return session.query(ChapterInfo).filter(ChapterInfo.book_id == book_id).order_by(ChapterInfo.start_page_number).all()

def _query_chapter_by_book_id_and_title(session: Session, book_id: int, title: str) -> Optional[ChapterInfo]:
    """Query chapter by book ID and title"""
    return session.query(ChapterInfo).filter(ChapterInfo.book_id == book_id, ChapterInfo.title == title).order_by(ChapterInfo.start_page_number).first()

def _query_chapter_by_book_id_and_exact_page_range(session: Session, book_id: int, start_page_number: int, end_page_number: int) -> Optional[ChapterInfo]:
    """Query chapter by book ID and exact page range"""
    return session.query(ChapterInfo).filter(ChapterInfo.book_id == book_id, ChapterInfo.start_page_number == start_page_number, ChapterInfo.end_page_number == end_page_number).order_by(ChapterInfo.start_page_number).first()

def _query_chapters_by_book_id_and_page_range(session: Session, book_id: int, start_page_number: int, end_page_number: int) -> List[ChapterInfo]:
    """Query chapters by book ID and page range"""
    return session.query(ChapterInfo).filter(ChapterInfo.book_id == book_id, ChapterInfo.start_page_number <= start_page_number, ChapterInfo.end_page_number >= end_page_number).order_by(ChapterInfo.start_page_number).all()

def _delete_chapters_by_book_id(session: Session, book_id: int) -> None:
    """Delete chapters by book ID"""
    session.query(ChapterInfo).filter(ChapterInfo.book_id == book_id).delete()
    session.commit()

# ------------------------------------------------------------
# Section related functions
# ------------------------------------------------------------

def _query_sections_by_book_id(session: Session, book_id: int) -> list[SectionInfo]:
    """Query sections by book ID"""
    return session.query(SectionInfo).filter(SectionInfo.book_id == book_id).order_by(SectionInfo.start_page_number).all()

def _query_sections_by_book_id_and_chapter_id(session: Session, book_id: int, chapter_id: int) -> list[SectionInfo]:
    """Query sections by chapter ID"""
    return session.query(SectionInfo).filter(SectionInfo.chapter_id == chapter_id).order_by(SectionInfo.start_page_number).all()

def _query_section_by_book_id_and_title(session: Session, book_id: int, title: str) -> Optional[SectionInfo]:
    """Query section by book ID and chapter ID and title"""
    return session.query(SectionInfo).filter(SectionInfo.book_id == book_id, SectionInfo.title == title).order_by(SectionInfo.start_page_number).first()

def _query_section_by_book_id_and_exact_page_range(session: Session, book_id: int, start_page_number: int, end_page_number: int) -> Optional[SectionInfo]:
    """Query section by book ID and exact page range"""
    return session.query(SectionInfo).filter(SectionInfo.book_id == book_id, SectionInfo.start_page_number == start_page_number, SectionInfo.end_page_number == end_page_number).order_by(SectionInfo.start_page_number).first()

def _query_sections_by_book_id_and_page_range(session: Session, book_id: int, start_page_number: int, end_page_number: int) -> List[SectionInfo]:
    """Query sections by book ID and page range"""
    return session.query(SectionInfo).filter(SectionInfo.book_id == book_id, SectionInfo.start_page_number <= start_page_number, SectionInfo.end_page_number >= end_page_number).order_by(SectionInfo.start_page_number).all()

def _delete_sections_by_book_id(session: Session, book_id: int) -> None:
    """Delete sections by book ID"""
    session.query(SectionInfo).filter(SectionInfo.book_id == book_id).delete()
    session.commit()

# ------------------------------------------------------------
# Page related functions
# ------------------------------------------------------------

def _query_pages_by_book_id(session: Session, book_id: int) -> list[PageInfo]:
    """Query pages by book ID"""
    return session.query(PageInfo).filter(PageInfo.book_id == book_id).order_by(PageInfo.page_number).all()

def _query_page_by_book_id_and_page_number(session: Session, book_id: int, page_number: int) -> Optional[PageInfo]:
    """Query page by book ID and page number"""
    return session.query(PageInfo).filter(PageInfo.book_id == book_id, PageInfo.page_number == page_number).order_by(PageInfo.page_number).first()

def _query_page_by_id(session: Session, page_id: int) -> Optional[PageInfo]:
    """Query page by ID"""
    return session.query(PageInfo).filter(PageInfo.page_id == page_id).first()