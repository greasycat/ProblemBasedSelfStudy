import { useState } from 'react';
import { bookApi } from '../services/api';
import { useBooks } from '../hooks/useBooks';
import { BookDetails } from '../components/BookDetails';
import { BookEdit } from '../components/BookEdit';
import { BookView } from '../components/BookView';
import { Sidebar } from '../components/Sidebar';
import { Chat } from '../components/Chat';
import type { Book } from '../types/api';

export function BooksPage() {
  const { books, loading, error, removeBook, updateBook, loadAllBooks, uploadBook, setError } = useBooks();
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [selectedBook, setSelectedBook] = useState<Book | null>(null);
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);
  const [bookToEdit, setBookToEdit] = useState<Book | undefined>();
  const [bookToViewPdf, setBookToViewPdf] = useState<Book | null>(null);
  
  // BookView state for visual alignment
  const [isBookViewOpen, setIsBookViewOpen] = useState(false);
  const [bookViewBook, setBookViewBook] = useState<Book | null>(null);
  const [bookViewPage, setBookViewPage] = useState<number>(0);

  const handleSelectBook = (book: Book) => {
    setSelectedBook(book);
  };

  const handleView = (book: Book) => {
    setSelectedBook(book);
    setIsDetailsOpen(true);
  };

  const handleEdit = (book: Book) => {
    setBookToEdit(book);
    setIsFormOpen(true);
  };

  const handleDelete = async (book: Book) => {
    if (window.confirm(`Are you sure you want to remove "${book.book_name || `Book ${book.book_id}`}"?`)) {
      try {
        await removeBook(book.book_id);
        if (selectedBook?.book_id === book.book_id) {
          setSelectedBook(null);
        }
      } catch (err) {
        // Error is handled by the hook
        console.error('Failed to delete book:', err);
      }
    }
  };

  const handleEditUpdate = (book: Book) => {
    updateBook(book);
    // Don't close the modal here - let BookEdit handle it after showing success
  };

  const handleEditClose = () => {
    setIsFormOpen(false);
    setBookToEdit(undefined);
  };

  const handleVisualAlign = (book: Book) => {
    // Open BookView with confirm popup for visual alignment
    setBookViewBook(book);
    // Start at page 0 or use alignment offset if it exists
    setBookViewPage(book.alignment_offset || 0);
    bookApi.getChapters(book.book_id || 0).then((response) => {
      const chapters = response.chapters;
      if (chapters.length > 0) {
        const firstChapterStartPageNumber = chapters[0].start_page_number;
        setBookViewPage(firstChapterStartPageNumber + (book.alignment_offset || 0));
      }
      else {
        console.log('No chapters found, setting to 0');
        setBookViewPage(0);
      }
    }).catch((error) => {
      console.log('Failed to get first chapter start page number:', error, 'setting to 0');
      setBookViewPage(0);
    });
    setIsBookViewOpen(true);
  };

  const handleVisualAlignConfirm = () => {
    // Visual alignment logic will be implemented later
    // For now, just close the view
    console.log('Visual align confirmed for book:', bookViewBook?.book_id, 'at page:', bookViewPage);


    bookApi.getChapters(bookViewBook?.book_id || 0).then((response) => {
        const chapters = response.chapters;
        if (chapters.length > 0) {
          const firstChapterStartPageNumber = chapters[0].start_page_number;
          console.log('First chapter start page number:', firstChapterStartPageNumber);
          setBookToEdit({
            ...bookToEdit!,
            alignment_offset: bookViewPage - firstChapterStartPageNumber,
          });
        }
      }).catch((error) => {
        console.error('Failed to get first chapter start page number:', error);
      });
  };

  return (
    <div className="flex h-screen relative">
      {/* Sidebar */}
      <div className="w-80 flex-shrink-0 relative z-10">
        <Sidebar
          books={books}
          loading={loading}
          error={error}
          selectedBook={selectedBook}
          onSelectBook={handleSelectBook}
          onView={handleView}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onViewPdf={(book) => setBookToViewPdf(book)}
          onUploadBook={uploadBook}
          onDismissError={() => setError(null)}
          onLoadBooks={loadAllBooks}
        />
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col min-w-0 relative z-20">
        <Chat selectedBook={selectedBook} bookToViewPdf={bookToViewPdf} onPdfViewClose={() => setBookToViewPdf(null)} />
      </div>

      {/* Modals */}
      <BookDetails
        isOpen={isDetailsOpen}
        onClose={() => {
          setIsDetailsOpen(false);
        }}
        book={selectedBook}
        onUpdate={updateBook}
      />
      <BookEdit
        isOpen={isFormOpen}
        onClose={handleEditClose}
        book={bookToEdit || null}
        onUpdate={handleEditUpdate}
        onVisualAlign={bookToEdit ? () => handleVisualAlign(bookToEdit) : undefined}
      />
      {bookViewBook && (
        <BookView
          isOpen={isBookViewOpen}
          onClose={() => {
            setIsBookViewOpen(false);
            setBookViewBook(null);
            setBookViewPage(0);
          }}
          bookId={bookViewBook.book_id}
          currentPage={bookViewPage}
          totalPages={bookViewBook.total_pages}
          onPageChange={setBookViewPage}
          showConfirmPopup={true}
          confirmQuestion="Is this page showing the first chapter of the book?"
          onConfirm={handleVisualAlignConfirm}
        />
      )}
    </div>
  );
}
