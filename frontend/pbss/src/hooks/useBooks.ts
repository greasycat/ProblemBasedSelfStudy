// Custom hook for book management
// This can be extended with more complex state management if needed

import { useState, useCallback } from 'react';
import { bookApi, ApiError } from '../services/api';
import type { Book } from '../types/api';

export function useBooks() {
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadBook = useCallback(async (bookId: number) => {
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

      setBooks((prev) => {
        const existing = prev.findIndex((b) => b.book_id === bookId);
        if (existing >= 0) {
          const updated = [...prev];
          updated[existing] = book;
          return updated;
        }
        return [...prev, book];
      });

      return book;
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Failed to load book';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const removeBook = useCallback(async (bookId: number) => {
    setLoading(true);
    setError(null);
    try {
      await bookApi.deleteBook(bookId);
      // Remove from local state
      setBooks((prev) => prev.filter((b) => b.book_id !== bookId));
    } catch (err) {
      const message = err instanceof ApiError 
        ? `Failed to delete book: ${err.message} (${err.status})`
        : err instanceof Error 
        ? `Failed to delete book: ${err.message}`
        : 'Failed to delete book';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const updateBook = useCallback((updatedBook: Book) => {
    setBooks((prev) => {
      const existing = prev.findIndex((b) => b.book_id === updatedBook.book_id);
      if (existing >= 0) {
        const updated = [...prev];
        updated[existing] = { ...updated[existing], ...updatedBook };
        return updated;
      }
      return [...prev, updatedBook];
    });
  }, []);

  const loadAllBooks = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await bookApi.getAllBooks();
      setBooks(response.books);
    } catch (err) {
      console.error('Failed to load books:', err);
      const message = err instanceof ApiError 
        ? `Failed to load books: ${err.message} (${err.status})`
        : err instanceof Error 
        ? `Failed to load books: ${err.message}`
        : 'Failed to load books';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  const uploadBook = useCallback(async (file: File) => {
    setLoading(true);
    setError(null);
    try {
      const response = await bookApi.uploadBook(file);
      
      // Load the uploaded book details
      const [totalPagesResponse, tocResponse] = await Promise.all([
        bookApi.getTotalPages(response.book_id),
        bookApi.checkTocExists(response.book_id).catch(() => ({ book_id: response.book_id, toc_exists: false })),
      ]);

      const book: Book = {
        book_id: response.book_id,
        total_pages: totalPagesResponse.total_pages,
        toc_exists: tocResponse.toc_exists,
      };

      setBooks((prev) => {
        const existing = prev.findIndex((b) => b.book_id === book.book_id);
        if (existing >= 0) {
          const updated = [...prev];
          updated[existing] = book;
          return updated;
        }
        return [...prev, book];
      });

      return book;
    } catch (err) {
      const message = err instanceof ApiError 
        ? `Failed to upload book: ${err.message} (${err.status})`
        : err instanceof Error 
        ? `Failed to upload book: ${err.message}`
        : 'Failed to upload book';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    books,
    loading,
    error,
    loadBook,
    removeBook,
    updateBook,
    loadAllBooks,
    uploadBook,
    setError,
  };
}

