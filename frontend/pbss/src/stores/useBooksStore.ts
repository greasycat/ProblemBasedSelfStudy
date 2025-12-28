import { create } from 'zustand';
import { bookApi, ApiError } from '../services/api';
import { useUIStore } from './useUIStore';
import type { Book } from '../types/api';

interface BooksState {
  /** Array of all books */
  books: Book[];
  /** Currently selected book */
  selectedBook: Book | null;
  
  // Synchronous Actions
  /** Set the books array */
  setBooks: (books: Book[]) => void;
  /** Select a book */
  selectBook: (book: Book | null) => void;
  /** Update a book in the books array */
  updateBook: (book: Book) => void;
  
  // Asynchronous Actions (API operations)
  /** Load a single book by ID from API */
  loadBook: (bookId: number) => Promise<Book>;
  /** Load all books from API */
  loadAllBooks: () => Promise<void>;
  /** Delete a book via API and remove from store */
  removeBook: (bookId: number) => Promise<void>;
  /** Upload a book file and add to store */
  uploadBook: (file: File) => Promise<Book>;
}

/**
 * Helper function to add or update a book in the array
 */
function addOrUpdateBookInArray(books: Book[], book: Book): Book[] {
  const existingIndex = books.findIndex((b) => b.book_id === book.book_id);
  if (existingIndex >= 0) {
    const updated = [...books];
    updated[existingIndex] = { ...updated[existingIndex], ...book };
    return updated;
  }
  return [...books, book];
}

export const useBooksStore = create<BooksState>((set) => {
  // Get UI store actions (we need to access it from outside to avoid circular dependency)
  // We'll access it within the async functions
  const getUIStore = () => useUIStore.getState();

  return {
    books: [],
    selectedBook: null,

    setBooks: (books) => set({ books }),

    selectBook: (selectedBook) => set({ selectedBook }),

    updateBook: (book) =>
      set((state) => ({
        books: addOrUpdateBookInArray(state.books, book),
      })),

    loadBook: async (bookId: number) => {
      const { setLoading, setError } = getUIStore();
      setLoading(true);
      setError(null);
      try {
        const [totalPagesResponse, tocResponse] = await Promise.all([
          bookApi.getTotalPages(bookId),
          bookApi.checkTocExists(bookId).catch(() => ({ book_id: bookId, toc_exists: false })),
        ]);

        const book: Book = {
          book_id: bookId,
          total_pages: totalPagesResponse.total_pages,
          toc_exists: tocResponse.toc_exists,
        };

        set((state) => ({
          books: addOrUpdateBookInArray(state.books, book),
        }));

        return book;
      } catch (err) {
        const message = err instanceof ApiError ? err.message : 'Failed to load book';
        setError(message);
        throw err;
      } finally {
        setLoading(false);
      }
    },

    loadAllBooks: async () => {
      const { setLoading, setError } = getUIStore();
      setLoading(true);
      setError(null);
      try {
        const response = await bookApi.getAllBooks();
        set({ books: response.books });
      } catch (err) {
        console.error('Failed to load books:', err);
        const message =
          err instanceof ApiError
            ? `Failed to load books: ${err.message} (${err.status})`
            : err instanceof Error
              ? `Failed to load books: ${err.message}`
              : 'Failed to load books';
        setError(message);
      } finally {
        setLoading(false);
      }
    },

    removeBook: async (bookId: number) => {
      const { setLoading, setError } = getUIStore();
      setLoading(true);
      setError(null);
      try {
        await bookApi.deleteBook(bookId);
        // Remove from store
        set((state) => {
          const filteredBooks = state.books.filter((b) => b.book_id !== bookId);
          const newSelectedBook =
            state.selectedBook?.book_id === bookId ? null : state.selectedBook;
          return { books: filteredBooks, selectedBook: newSelectedBook };
        });
      } catch (err) {
        const message =
          err instanceof ApiError
            ? `Failed to delete book: ${err.message} (${err.status})`
            : err instanceof Error
              ? `Failed to delete book: ${err.message}`
              : 'Failed to delete book';
        setError(message);
        throw err;
      } finally {
        setLoading(false);
      }
    },

    uploadBook: async (file: File) => {
      const { setLoading, setError } = getUIStore();
      setLoading(true);
      setError(null);
      try {
        const response = await bookApi.uploadBook(file);

        // Load the uploaded book details
        const [totalPagesResponse, tocResponse] = await Promise.all([
          bookApi.getTotalPages(response.book_id),
          bookApi
            .checkTocExists(response.book_id)
            .catch(() => ({ book_id: response.book_id, toc_exists: false })),
        ]);

        const book: Book = {
          book_id: response.book_id,
          total_pages: totalPagesResponse.total_pages,
          toc_exists: tocResponse.toc_exists,
        };

        set((state) => ({
          books: addOrUpdateBookInArray(state.books, book),
        }));

        return book;
      } catch (err) {
        const message =
          err instanceof ApiError
            ? `Failed to upload book: ${err.message} (${err.status})`
            : err instanceof Error
              ? `Failed to upload book: ${err.message}`
              : 'Failed to upload book';
        setError(message);
        throw err;
      } finally {
        setLoading(false);
      }
    },
  };
});

