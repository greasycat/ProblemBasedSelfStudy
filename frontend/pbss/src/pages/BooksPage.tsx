import { useState } from 'react';
import { useBooks } from '../hooks/useBooks';
import { BookDetails } from '../components/BookDetails';
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

  const handleFormSubmit = (book: Book) => {
    updateBook(book);
    setIsFormOpen(false);
    setBookToEdit(undefined);
  };

  const handleFormClose = () => {
    setIsFormOpen(false);
    setBookToEdit(undefined);
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
    </div>
  );
}
