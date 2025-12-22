// Custom hook for book management
// This can be extended with more complex state management if needed

import { useState, useCallback } from 'react';
import { bookApi, ApiError } from '../services/api';
import type { Book } from '../types/api';

export function useBooks() {
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadBook = useCallback(async (pdfPath: string) => {
    setLoading(true);
    setError(null);
    try {
      const [totalPagesResponse, tocResponse] = await Promise.all([
        bookApi.getTotalPages({ pdf_path: pdfPath }),
        bookApi.checkTocExists(pdfPath).catch(() => ({ pdf_path: pdfPath, toc_exists: false })),
      ]);

      const book: Book = {
        pdf_path: pdfPath,
        total_pages: totalPagesResponse.total_pages,
        toc_exists: tocResponse.toc_exists,
      };

      setBooks((prev) => {
        const existing = prev.findIndex((b) => b.pdf_path === pdfPath);
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

  const removeBook = useCallback((pdfPath: string) => {
    setBooks((prev) => prev.filter((b) => b.pdf_path !== pdfPath));
  }, []);

  const updateBook = useCallback((updatedBook: Book) => {
    setBooks((prev) => {
      const existing = prev.findIndex((b) => b.pdf_path === updatedBook.pdf_path);
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

  return {
    books,
    loading,
    error,
    loadBook,
    removeBook,
    updateBook,
    loadAllBooks,
    setError,
  };
}

