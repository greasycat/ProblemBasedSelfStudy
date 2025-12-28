import { useState, useCallback } from 'react';
import { bookApi } from '../services/api';
import { useBooksStore } from '../stores/useBooksStore';
import { useModalStore, type ModalState, DEFAULT_MODAL_STATE } from '../stores/useModalStore';
import { useBookViewStore } from '../stores/useBookViewStore';
import { BookDetails } from '../components/BookDetails';
import { BookEdit } from '../components/BookEdit';
import { BookView } from '../components/BookView';
import { Sidebar } from '../components/Sidebar';
import { Chat } from '../components/Chat';
import type { Book } from '../types/api';

// Modal keys for consistent modal identification
const MODAL_KEYS = {
  EDIT_BOOK: 'editBook',
  BOOK_DETAILS: 'bookDetails',
} as const;

export function BooksPage() {
  // Get state and operations from stores
  const { selectedBook, selectBook, removeBook, updateBook } = useBooksStore();
  const { openModal, closeModal } = useModalStore();
  const { state: bookViewState, close: closeBookView, setPage, openForVisualAlignment } = useBookViewStore();
  
  // Memoize selectors to prevent infinite loops
  // Zustand needs stable selector function references
  const editModalSelector = useCallback(
    (state: { modals: Record<string, ModalState> }) =>
      state.modals[MODAL_KEYS.EDIT_BOOK] || DEFAULT_MODAL_STATE,
    []
  );
  const detailsModalSelector = useCallback(
    (state: { modals: Record<string, ModalState> }) =>
      state.modals[MODAL_KEYS.BOOK_DETAILS]?.isOpen ?? false,
    []
  );
  
  // Get modal states reactively using memoized selectors
  const editModalState = useModalStore(editModalSelector) as ModalState<Book>;
  const detailsModalIsOpen = useModalStore(detailsModalSelector);
  
  // PDF view state (used for Chat component)
  const [bookToViewPdf, setBookToViewPdf] = useState<Book | null>(null);

  const handleView = (book: Book) => {
    selectBook(book);
    openModal(MODAL_KEYS.BOOK_DETAILS, book);
  };

  const handleEdit = (book: Book) => {
    openModal(MODAL_KEYS.EDIT_BOOK, book);
  };

  const handleDelete = async (book: Book) => {
    if (window.confirm(`Are you sure you want to remove "${book.book_name || `Book ${book.book_id}`}"?`)) {
      try {
        await removeBook(book.book_id);
        // selectedBook is automatically cleared in the store if it was the deleted book
      } catch (err) {
        // Error is handled by the hook and store
        console.error('Failed to delete book:', err);
      }
    }
  };

  const handleEditUpdate = (book: Book) => {
    updateBook(book);
    // Don't close the modal here - let BookEdit handle it after showing success
  };

  const handleVisualAlign = (book: Book) => {
    // Open BookView for visual alignment
    openForVisualAlignment(book);
  };

  const handleVisualAlignConfirm = async () => {
    // Calculate alignment offset based on current page and first chapter
    if (!bookViewState.book) return;

    try {
      const response = await bookApi.getChapters(bookViewState.book.book_id || 0);
      const chapters = response.chapters;
      if (chapters.length > 0 && editModalState.data) {
        const firstChapterStartPageNumber = chapters[0].start_page_number;
        const alignmentOffset = bookViewState.currentPage - firstChapterStartPageNumber;
        
        // Update the book in edit modal with new alignment offset
        const updatedBook: Book = {
          ...editModalState.data,
          alignment_offset: alignmentOffset,
        };
        updateBook(updatedBook);
        
        // Update edit modal data to reflect the change
        openModal(MODAL_KEYS.EDIT_BOOK, updatedBook);
      }
    } catch (error) {
      console.error('Failed to get first chapter start page number:', error);
    }
  };

  return (
    <div className="flex h-screen relative">
      {/* Sidebar */}
      <div className="w-80 flex-shrink-0 relative z-10">
        <Sidebar
          onView={handleView}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onViewPdf={(book) => setBookToViewPdf(book)}
        />
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col min-w-0 relative z-20">
        <Chat bookToViewPdf={bookToViewPdf} onPdfViewClose={() => setBookToViewPdf(null)} />
      </div>

      {/* Modals */}
      <BookDetails
        isOpen={detailsModalIsOpen}
        onClose={() => closeModal(MODAL_KEYS.BOOK_DETAILS)}
        book={selectedBook}
        onUpdate={updateBook}
      />
      <BookEdit
        isOpen={editModalState.isOpen}
        onClose={() => closeModal(MODAL_KEYS.EDIT_BOOK)}
        book={(editModalState.data as Book | null) || null}
        onUpdate={handleEditUpdate}
        onVisualAlign={editModalState.data ? () => handleVisualAlign(editModalState.data as Book) : undefined}
      />
      {bookViewState.book && (
        <BookView
          isOpen={bookViewState.isOpen}
          onClose={closeBookView}
          bookId={bookViewState.book.book_id}
          currentPage={bookViewState.currentPage}
          totalPages={bookViewState.book.total_pages}
          onPageChange={setPage}
          showConfirmPopup={true}
          confirmQuestion="Is this page showing the first chapter of the book?"
          onConfirm={handleVisualAlignConfirm}
        />
      )}
    </div>
  );
}
