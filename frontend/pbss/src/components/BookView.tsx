import { useEffect } from 'react';
import { Button } from './Button';
import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline';

interface BookViewProps {
  isOpen: boolean;
  onClose: () => void;
  bookId: number;
  currentPage: number;
  totalPages?: number;
  onPageChange: (page: number) => void;
  // alignmentOffset?: number;
}

export function BookView({
  isOpen,
  onClose,
  bookId,
  currentPage,
  totalPages,
  onPageChange,
  // alignmentOffset = 0,
}: BookViewProps) {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    if (isOpen) {
      window.addEventListener('keydown', handleEscape);
      return () => window.removeEventListener('keydown', handleEscape);
    }
  }, [isOpen, onClose]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen || e.key === 'Escape') return;
      if (e.key === 'ArrowLeft' && currentPage > 0) {
        e.preventDefault();
        onPageChange(currentPage - 1);
      } else if (e.key === 'ArrowRight' && (totalPages === undefined || currentPage < totalPages - 1)) {
        e.preventDefault();
        onPageChange(currentPage + 1);
      }
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen, currentPage, totalPages, onPageChange]);

  const handlePreviousPage = () => {
    if (currentPage > 0) {
      onPageChange(currentPage - 1);
    }
  };

  const handleNextPage = () => {
    if (totalPages === undefined || currentPage < totalPages - 1) {
      onPageChange(currentPage + 1);
    }
  };

  if (!isOpen) return null;

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
  // currentPage may include alignment offset, so we subtract it for the API call
  // API expects 0-indexed page number without alignment offset
  const apiPageNumber = Math.max(0, currentPage);
  const displayPageNumber = currentPage; // currentPage already includes alignment offset for display
  const imageUrl = `${API_BASE_URL}/page-image-binary?book_id=${bookId}&page_number=${apiPageNumber}`;

  // Navigation bounds: currentPage should be >= alignmentOffset and <= (totalPages - 1 + alignmentOffset)
  const minPage = 0;
  const maxPage = totalPages !== undefined ? (totalPages - 1) : undefined;
  const canGoPrevious = currentPage > minPage;
  const canGoNext = maxPage === undefined || currentPage < maxPage;

  return (
    <div 
      className="fixed inset-0 flex items-center justify-center z-[1000] p-4"
      style={{ backgroundColor: 'transparent' }}
      onClick={onClose}
    >
      <div 
        className="relative bg-white rounded-xl max-w-6xl w-full max-h-[90vh] flex flex-col shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <div className="absolute top-2 right-2 z-10">
          <Button variant="ghost" size="small" onClick={onClose}>
            ×
          </Button>
        </div>

        {/* Image Container */}
        <div className="w-full h-[90vh] flex items-center justify-center bg-gray-100 relative">
          {/* Left Navigation Button */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              handlePreviousPage();
            }}
            disabled={!canGoPrevious}
            className={`absolute left-4 top-1/2 -translate-y-1/2 z-10 p-2 rounded-full bg-white/90 hover:bg-white shadow-lg transition-all ${
              canGoPrevious ? 'cursor-pointer' : 'cursor-not-allowed opacity-50'
            }`}
            aria-label="Previous page"
          >
            <ChevronLeftIcon className="w-6 h-6 text-gray-800" />
          </button>

          {/* Image */}
          <img
            src={imageUrl}
            alt={`Page ${displayPageNumber + 1}`}
            className="max-w-full max-h-full object-contain"
          />

          {/* Right Navigation Button */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleNextPage();
            }}
            disabled={!canGoNext}
            className={`absolute right-4 top-1/2 -translate-y-1/2 z-10 p-2 rounded-full bg-white/90 hover:bg-white shadow-lg transition-all ${
              canGoNext ? 'cursor-pointer' : 'cursor-not-allowed opacity-50'
            }`}
            aria-label="Next page"
          >
            <ChevronRightIcon className="w-6 h-6 text-gray-800" />
          </button>
        </div>

        {/* Page Indicator */}
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-black/70 text-white px-4 py-2 rounded-lg text-sm font-medium">
          {totalPages !== undefined 
            ? `Page ${displayPageNumber + 1} of ${totalPages}`
            : `Page ${displayPageNumber + 1}`
          }
        </div>
      </div>
    </div>
  );
}

