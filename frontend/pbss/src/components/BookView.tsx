import { useEffect, useState } from 'react';
import { Button } from './Button';
import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline';
import { bookApi } from '../services/api';

interface BookViewProps {
  isOpen: boolean;
  onClose: () => void;
  bookId: number;
  currentPage: number;
  totalPages?: number;
  onPageChange: (page: number) => void;
  // Optional confirm popup props
  showConfirmPopup?: boolean;
  confirmQuestion?: string;
  onConfirm?: () => void;
  // alignmentOffset?: number;
}

export function BookView({
  isOpen,
  onClose,
  bookId,
  currentPage,
  totalPages,
  onPageChange,
  showConfirmPopup = false,
  confirmQuestion = 'Is this the correct page?',
  onConfirm,
  // alignmentOffset = 0,
}: BookViewProps) {
  const [isConfirmPopupVisible, setIsConfirmPopupVisible] = useState(showConfirmPopup);
  const [canGoPrevious, setCanGoPrevious] = useState(false);
  const [canGoNext, setCanGoNext] = useState(true);
  const [checkingPages, setCheckingPages] = useState(false);

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      // Reset confirm popup visibility when BookView opens
      if (showConfirmPopup) {
        setIsConfirmPopupVisible(true);
      }
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen, showConfirmPopup]);

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

  // Check if pages exist by calling the API
  useEffect(() => {
    if (!isOpen || !bookId) return;

    const checkPageExists = async (pageNumber: number): Promise<boolean> => {
      try {
        await bookApi.getPageImage({ book_id: bookId, page_number: pageNumber, dpi: 150 });
        return true;
      } catch (error) {
        return false;
      }
    };

    const checkNavigationAvailability = async () => {
      setCheckingPages(true);
      
      // Check previous page
      const prevPageExists = currentPage > 0 ? await checkPageExists(currentPage - 1) : false;
      setCanGoPrevious(prevPageExists);
      
      // Check next page
      const nextPageExists = await checkPageExists(currentPage + 1);
      setCanGoNext(nextPageExists);
      
      setCheckingPages(false);
    };

    checkNavigationAvailability();
  }, [isOpen, bookId, currentPage]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen || e.key === 'Escape' || checkingPages) return;
      if (e.key === 'ArrowLeft' && canGoPrevious) {
        e.preventDefault();
        onPageChange(currentPage - 1);
      } else if (e.key === 'ArrowRight' && canGoNext) {
        e.preventDefault();
        onPageChange(currentPage + 1);
      }
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen, currentPage, canGoPrevious, canGoNext, onPageChange, checkingPages]);

  const handlePreviousPage = () => {
    if (canGoPrevious) {
      onPageChange(currentPage - 1);
    }
  };

  const handleNextPage = () => {
    if (canGoNext) {
      onPageChange(currentPage + 1);
    }
  };

  const handlePrevious5Pages = () => {
    const newPage = Math.max(0, currentPage - 5);
    if (newPage !== currentPage) {
      onPageChange(newPage);
    }
  };

  const handleNext5Pages = () => {
    // Try to go forward 5 pages - will be checked by API on page change
    onPageChange(currentPage + 5);
  };

  if (!isOpen) return null;

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
  // currentPage may include alignment offset, so we subtract it for the API call
  // API expects 0-indexed page number without alignment offset
  const apiPageNumber = Math.max(0, currentPage);
  const displayPageNumber = currentPage; // currentPage already includes alignment offset for display
  const imageUrl = `${API_BASE_URL}/page-image-binary?book_id=${bookId}&page_number=${apiPageNumber}`;

  const handleConfirm = () => {
    setIsConfirmPopupVisible(false);
    if (onConfirm) {
      onConfirm();
    }
    onClose();
  };

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
        {/* Confirm Popup */}
        {isConfirmPopupVisible && (
          <div className="absolute top-4 left-1/2 -translate-x-1/2 z-20 bg-white rounded-lg shadow-2xl border-2 border-primary p-4 min-w-[300px]">
            <div className="flex flex-col gap-3">
              <p className="text-text-primary font-medium text-base m-0">
                {confirmQuestion}
              </p>
              <div className="flex justify-end gap-2">
                <Button variant="primary" size="small" onClick={handleConfirm}>
                  Confirm
                </Button>
              </div>
            </div>
          </div>
        )}

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
            disabled={!canGoPrevious || checkingPages}
            className={`absolute left-4 top-1/2 -translate-y-1/2 z-10 p-2 rounded-full bg-white/90 hover:bg-white shadow-lg transition-all ${
              canGoPrevious && !checkingPages ? 'cursor-pointer' : 'cursor-not-allowed opacity-50'
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
            disabled={!canGoNext || checkingPages}
            className={`absolute right-4 top-1/2 -translate-y-1/2 z-10 p-2 rounded-full bg-white/90 hover:bg-white shadow-lg transition-all ${
              canGoNext && !checkingPages ? 'cursor-pointer' : 'cursor-not-allowed opacity-50'
            }`}
            aria-label="Next page"
          >
            <ChevronRightIcon className="w-6 h-6 text-gray-800" />
          </button>

          {/* -5 Pages Navigation Button */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              handlePrevious5Pages();
            }}
            disabled={!canGoPrevious || checkingPages}
            className={`absolute left-4 top-[calc(50%+60px)] -translate-y-1/2 z-10 p-2 rounded-full bg-white/90 hover:bg-white shadow-lg transition-all text-sm font-medium ${
              canGoPrevious && !checkingPages ? 'cursor-pointer' : 'cursor-not-allowed opacity-50'
            }`}
            aria-label="Previous 5 pages"
          >
            -5
          </button>

          {/* +5 Pages Navigation Button */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleNext5Pages();
            }}
            disabled={!canGoNext || checkingPages}
            className={`absolute right-4 top-[calc(50%+60px)] -translate-y-1/2 z-10 p-2 rounded-full bg-white/90 hover:bg-white shadow-lg transition-all text-sm font-medium ${
              canGoNext && !checkingPages ? 'cursor-pointer' : 'cursor-not-allowed opacity-50'
            }`}
            aria-label="Next 5 pages"
          >
            +5
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

