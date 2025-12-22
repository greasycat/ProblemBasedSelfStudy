import { useState, useEffect } from 'react';
import type { Book } from '../types/api';
import { Button } from './Button';
import { healthApi } from '../services/api';
import { PencilSquareIcon, TrashIcon } from '@heroicons/react/24/outline';

interface SidebarProps {
  books: Book[];
  loading: boolean;
  error: string | null;
  selectedBook: Book | null;
  onSelectBook: (book: Book) => void;
  onView: (book: Book) => void;
  onEdit: (book: Book) => void;
  onDelete: (book: Book) => void;
  onAddBook: () => void;
  onDismissError: () => void;
  onLoadBooks?: () => void;
}

export function Sidebar({
  books,
  loading,
  error,
  selectedBook,
  onSelectBook,
  onEdit,
  onDelete,
  onAddBook,
  onDismissError,
  onLoadBooks,
}: SidebarProps) {
  const [healthStatus, setHealthStatus] = useState<{
    status: string;
    llm_initialized: boolean;
    context_initialized: boolean;
  } | null>(null);

  useEffect(() => {
    // Check backend health on mount
    healthApi
      .check()
      .then(setHealthStatus)
      .catch(() => {
        setHealthStatus({ status: 'unhealthy', llm_initialized: false, context_initialized: false });
      });
    
    // Load books from database on mount
    if (onLoadBooks) {
      onLoadBooks();
    }
  }, [onLoadBooks]);

  return (
    <div className="flex flex-col h-full bg-lightYellow shadow-sm">
      {/* Sidebar Header */}
      <div className="px-4 pt-6 bg-background-off">
        <div className="flex justify-end items-center h-full w-full">
          <Button variant="primary" size="full" onClick={onAddBook} className="self-center">
            + Add
          </Button>
        </div>
        {error && (
          <div className="mt-2 text-sm text-error bg-red-50 border border-red-200 rounded px-3 py-2 shadow-sm">
            {error}
            <button
              onClick={onDismissError}
              className="ml-2 text-red-600 hover:text-red-800 font-semibold"
            >
              ×
            </button>
          </div>
        )}
      </div>

      {/* Books List */}
      <div className="flex-1 overflow-y-auto py-4">
        {loading && books.length === 0 ? (
          <div className="text-center py-8 text-text-secondary">Loading books...</div>
        ) : books.length === 0 ? (
          <div className="text-center py-8 text-text-secondary">
            <p className="mb-2">No books found</p>
            <p className="text-sm">Add your first book to get started!</p>
          </div>
        ) : (
          <div>
            {books.map((book) => (
              <div
                key={book.pdf_path}
                onClick={() => onSelectBook(book)}
              >
                <div className={`bg-background-off rounded-lg p-4 transition-shadow ${
                  selectedBook?.pdf_path === book.pdf_path
                    ? 'bg-gray-200'
                    : 'hover:opacity-80'
                }`}>
                  <div className="flex justify-between items-start gap-2">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-text-primary mb-1 truncate">
                        {book.book_name || book.pdf_path.split('/').pop() || book.pdf_path}
                      </h3>
                      {book.book_author && (
                        <p className="text-sm text-text-secondary truncate opacity-60">
                          {book.book_author}
                        </p>
                      )}
                    </div>
                    <div className="flex gap-1 flex-shrink-0">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onEdit(book);
                        }}
                        className="p-1.5 text-text-secondary hover:text-primary transition-colors rounded hover:bg-background-subtle"
                        aria-label="Edit book"
                      >
                        <PencilSquareIcon className="w-5 h-5" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onDelete(book);
                        }}
                        className="p-1.5 text-text-secondary hover:text-error transition-colors rounded hover:bg-background-subtle"
                        aria-label="Delete book"
                      >
                        <TrashIcon className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Health Status Footer */}
      {healthStatus && (
        <div className="px-6 py-3 shadow-lg bg-background-off border-t border-gray-200">
          <div className="flex items-center gap-2 text-xs text-text-secondary">
            <span
              className={`text-sm ${
                healthStatus.status === 'healthy' ? 'text-success opacity-100' : 'opacity-60'
              }`}
            >
              {healthStatus.status === 'healthy' ? '●' : '○'}
            </span>
            <span>
              Backend {healthStatus.status}
              {healthStatus.llm_initialized && healthStatus.context_initialized
                ? ' (Ready)'
                : ' (Initializing...)'}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
