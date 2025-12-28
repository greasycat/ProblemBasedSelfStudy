import { useState, useEffect, useRef } from 'react';
import type { Book } from '../types/api';
import { useBooksStore } from '../stores/useBooksStore';
import { useUIStore } from '../stores/useUIStore';
import { useModalStore } from '../stores/useModalStore';
import { useToastStore } from '../stores/useToastStore';
import { useGuidanceStore, Instruction } from '../stores/useGuidanceStore';
import { useBookViewStore } from '../stores/useBookViewStore';
import { Button } from './Button';
import { healthApi, bookApi } from '../services/api';
import { PencilSquareIcon, TrashIcon, ArrowUpTrayIcon, DocumentTextIcon } from '@heroicons/react/24/outline';

// Modal key for edit book modal
const MODAL_KEY_EDIT_BOOK = 'EDIT_BOOK';

export function Sidebar() {
  // Get state and operations from stores
  const { books, selectedBook, selectBook, loadAllBooks, uploadBook, removeBook } = useBooksStore();
  const { loading, error, clearError, setPdfViewBook } = useUIStore();
  const { openModal } = useModalStore();
  const { showToast } = useToastStore();
  const { setInstructions, openGuidance } = useGuidanceStore();
  const { openForVisualAlignment } = useBookViewStore();
  const [healthStatus, setHealthStatus] = useState<{
    status: string;
    llm_initialized: boolean;
    context_initialized: boolean;
  } | null>(null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollingIntervalRef = useRef<number | null>(null);
  const pollingBookIdRef = useRef<number | null>(null);

  const capitalizeFirstLetterOfEachWord = (sentence: string) => {
    return sentence
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }

  useEffect(() => {
    // Check backend health on mount
    healthApi
      .check()
      .then(setHealthStatus)
      .catch(() => {
        setHealthStatus({ status: 'unhealthy', llm_initialized: false, context_initialized: false });
      });
    
    // Load books from database on mount
    loadAllBooks();

    // Cleanup polling interval on unmount
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
      pollingBookIdRef.current = null;
    };
  }, [loadAllBooks]);

  // Watch for uploaded book to get a name
  useEffect(() => {
    if (pollingBookIdRef.current) {
      const book = books.find((b) => b.book_id === pollingBookIdRef.current);
      if (book?.book_name) {
        // Book name is now available, stop polling
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
        pollingBookIdRef.current = null;
        setUploading(false);
        
        // Show guidance instead of edit modal
        const handleUpdateToc = async () => {
          if (!book) return;
          try {
            showToast('Extracting TOC...', 'info');
            await bookApi.updateToc({ 
              book_id: book.book_id, 
              caching: true, 
              overwrite: false 
            });
            showToast('TOC extracted successfully!', 'success');
            // Reload books to update TOC status
            await loadAllBooks();
          } catch (err) {
            console.error('Failed to update TOC:', err);
            showToast('Failed to extract TOC', 'error');
          }
        };

        const handleVisualAlign = async () => {
          if (!book) return;
          try {
            await openForVisualAlignment(book);
            // Close guidance when opening visual alignment
            useGuidanceStore.getState().closeGuidance();
          } catch (err) {
            console.error('Failed to open visual alignment:', err);
            showToast('Failed to open visual alignment', 'error');
          }
        };

        // Create guidance instructions
        const instructions = [
          new Instruction(
            "You've successfully uploaded a book, next step is to extract the TOC",
            [handleUpdateToc],
            ["Update TOC"]
          ),
          new Instruction(
            "You will need to visually align the book",
            [handleVisualAlign],
            ["Visual Align"]
          ),
        ];

        setInstructions(instructions);
        openGuidance();
      }
    }
  }, [books, openModal, setInstructions, openGuidance, showToast, loadAllBooks, openForVisualAlignment]);

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      alert('Please select a PDF file');
      return;
    }

    setUploading(true);
    try {
      showToast('Uploading takes a few seconds...', 'info');
      const uploadedBook = await uploadBook(file);
      const bookId = uploadedBook.book_id;

      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }

      // Start polling until book_name is available
      // Clear any existing polling interval
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }

      // Set the book ID we're waiting for
      pollingBookIdRef.current = bookId;

      // Initial load
      await loadAllBooks();

        // Start polling every 1 second
        const maxAttempts = 60; // Maximum polling attempts (60 * 1s = 60 seconds)
        let attempts = 0;


        pollingIntervalRef.current = setInterval(() => {
          attempts++;
          if (attempts >= maxAttempts) {
            // Max attempts reached, stop polling
            if (pollingIntervalRef.current) {
              clearInterval(pollingIntervalRef.current);
              pollingIntervalRef.current = null;
            }
            pollingBookIdRef.current = null;
            setUploading(false);
          } else {
            // Continue polling
            loadAllBooks();
          }
        }, 1000); // Poll every 1 second
    } catch (err) {
      // Error is handled by the hook
      showToast('Upload failed', 'error');
      // Clean up polling state on error
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
      pollingBookIdRef.current = null;
      setUploading(false);
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleEdit = (book: Book) => {
    openModal(MODAL_KEY_EDIT_BOOK, { book, isNew: false });
  };

  const handleDelete = async (book: Book) => {
    if (window.confirm(`Are you sure you want to remove "${book.book_name || `Book ${book.book_id}`}"?`)) {
      try {
        await removeBook(book.book_id);
      } catch (err) {
        console.error('Failed to delete book:', err);
      }
    }
  };

  const handleViewPdf = (book: Book) => {
    setPdfViewBook(book);
  };

  return (
    <div className="flex flex-col h-full bg-lightYellow shadow-sm">
      {/* Sidebar Header */}
      <div className="px-4 pt-6 bg-background-off">
        <div className="flex flex-col gap-2">
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            onChange={handleFileSelect}
            className="hidden"
            disabled={uploading || loading}
          />
          <Button 
            variant="ghost" 
            size="full" 
            onClick={handleUploadClick} 
            className="self-center justify-center"
            disabled={uploading || loading}
            isLoading={uploading}
          >
            <ArrowUpTrayIcon className="w-6 h-6 text-primary" />
            <span className="font-bold text-primary">Upload PDF</span>
          </Button>
        </div>
        {error && (
          <div className="mt-2 text-sm text-error bg-red-50 border border-red-200 rounded px-3 py-2 shadow-sm">
            {error}
            <button
              onClick={clearError}
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
                key={book.book_id}
                onClick={() => selectBook(book)}
              >
                <div className={`bg-background-off rounded-lg p-4 transition-all duration-100 ${
                  selectedBook?.book_id === book.book_id
                    ? 'border-r-4 border-primary bg-background-subtle'
                    : 'hover:bg-background-subtle hover:cursor-pointer'
                }`}>
                  <div className="flex justify-between items-start gap-2">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-text-primary mb-1 truncate">
                        {capitalizeFirstLetterOfEachWord(book.book_name || `Unknown Book ${book.book_id}`)}
                      </h3>
                      {book.book_author && (
                        <p className="text-sm text-text-secondary truncate opacity-60">
                          {capitalizeFirstLetterOfEachWord(book.book_author)}
                        </p>
                      )}
                    </div>
                    <div className="flex gap-1 flex-shrink-0">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleViewPdf(book);
                        }}
                        className="p-1.5 text-text-secondary hover:text-primary transition-colors rounded hover:bg-background-subtle"
                        aria-label="View PDF"
                      >
                        <DocumentTextIcon className="w-5 h-5" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleEdit(book);
                        }}
                        className="p-1.5 text-text-secondary hover:text-primary transition-colors rounded hover:bg-background-subtle"
                        aria-label="Edit book"
                      >
                        <PencilSquareIcon className="w-5 h-5" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete(book);
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
