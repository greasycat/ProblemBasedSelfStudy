import { useState } from 'react';
import { useBooks } from '../hooks/useBooks';
import { BookForm } from '../components/BookForm';
import { BookDetails } from '../components/BookDetails';
import { Sidebar } from '../components/Sidebar';
import { Chat } from '../components/Chat';
import type { Book } from '../types/api';

export function BooksPage() {
  const { books, loading, error, removeBook, updateBook, loadAllBooks, setError } = useBooks();
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [selectedBook, setSelectedBook] = useState<Book | null>(null);
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);
  const [bookToEdit, setBookToEdit] = useState<Book | undefined>();

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
    if (window.confirm(`Are you sure you want to remove "${book.pdf_path}"?`)) {
      removeBook(book.pdf_path);
      if (selectedBook?.pdf_path === book.pdf_path) {
        setSelectedBook(null);
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
    <div className="flex h-screen">
      {/* Sidebar */}
      <div className="w-80 flex-shrink-0">
        <Sidebar
          books={books}
          loading={loading}
          error={error}
          selectedBook={selectedBook}
          onSelectBook={handleSelectBook}
          onView={handleView}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onAddBook={() => setIsFormOpen(true)}
          onDismissError={() => setError(null)}
          onLoadBooks={loadAllBooks}
        />
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <Chat selectedBook={selectedBook} />
      </div>

      {/* Modals */}
      <BookForm
        isOpen={isFormOpen}
        onClose={handleFormClose}
        onSubmit={handleFormSubmit}
        initialBook={bookToEdit}
      />

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
