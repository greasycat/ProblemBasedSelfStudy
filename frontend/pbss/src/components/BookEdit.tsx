import { useState, useEffect, useCallback } from 'react';
import { Modal } from './Modal';
import { Button } from './Button';
import { Input } from './Input';
import { Alert } from './Alert';
import { bookApi } from '../services/api';
import { useModalStore, type ModalState, DEFAULT_MODAL_STATE } from '../stores/useModalStore';
import { useBooksStore } from '../stores/useBooksStore';
import { useBookViewStore } from '../stores/useBookViewStore';
import type { Book } from '../types/api';

// Modal key for edit book modal
const EDIT_BOOK_MODAL_KEY = 'EDIT_BOOK';

// Type for edit modal data
type EditModalData = { book: Book; isNew: boolean };

export function BookEdit() {
  // Get modal state from store
  const editModalSelector = useCallback(
    (state: { modals: Record<string, ModalState> }) =>
      state.modals[EDIT_BOOK_MODAL_KEY] || DEFAULT_MODAL_STATE,
    []
  );
  const editModalState = useModalStore(editModalSelector) as ModalState<EditModalData>;
  const closeModal = useModalStore((state) => state.closeModal);
  
  // Get book and modal state
  const book = editModalState.data?.book || null;
  const isNewBook = editModalState.data?.isNew || false;
  const isOpen = editModalState.isOpen;
  
  // Get store actions
  const updateBook = useBooksStore((state) => state.updateBook);
  const openForVisualAlignment = useBookViewStore((state) => state.openForVisualAlignment);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Form state
  const [title, setTitle] = useState('');
  const [author, setAuthor] = useState('');
  const [keywords, setKeywords] = useState('');
  const [alignmentOffset, setAlignmentOffset] = useState<string>('');

  // Initialize form fields when book changes or modal opens
  useEffect(() => {
    if (isOpen && book) {
      setTitle(book.book_name || '');
      setAuthor(book.book_author || '');
      setKeywords(book.book_keywords || '');
      setAlignmentOffset(book.alignment_offset?.toString() || '');
      setError(null);
      setSuccess(null);
    }
  }, [isOpen, book?.book_id, book?.alignment_offset, book?.book_name, book?.book_author, book?.book_keywords]);

  const handleSave = async () => {
    if (!book) return;

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // Build update request with only changed fields
      const updateRequest: {
        book_id: number;
        book_name?: string;
        book_author?: string;
        book_keywords?: string;
        alignment_offset?: number;
      } = {
        book_id: book.book_id,
      };

      // Only include fields that have been modified
      if (title !== (book.book_name || '')) {
        updateRequest.book_name = title;
      }
      if (author !== (book.book_author || '')) {
        updateRequest.book_author = author;
      }
      if (keywords !== (book.book_keywords || '')) {
        updateRequest.book_keywords = keywords;
      }
      
      const offsetValue = alignmentOffset.trim() === '' ? undefined : parseInt(alignmentOffset, 10);
      if (offsetValue !== undefined && !isNaN(offsetValue)) {
        if (!isNaN(offsetValue)) {
          updateRequest.alignment_offset = offsetValue;
        }
      }

      // Check if there are any changes
      if (Object.keys(updateRequest).length === 1) {
        setError('No changes to save');
        console.log(updateRequest);
        setLoading(false);
        return;
      }

      // Validate alignment offset if provided
      if (updateRequest.alignment_offset !== undefined && isNaN(updateRequest.alignment_offset)) {
        setError('Alignment offset must be a valid number');
        setLoading(false);
        return;
      }

      await bookApi.updateBookFields(updateRequest);
      
      setSuccess('Book information updated successfully');
      
      // Update the book object with new values
      const updatedBook: Book = {
        ...book,
        book_name: updateRequest.book_name !== undefined ? updateRequest.book_name : book.book_name,
        book_author: updateRequest.book_author !== undefined ? updateRequest.book_author : book.book_author,
        book_keywords: updateRequest.book_keywords !== undefined ? updateRequest.book_keywords : book.book_keywords,
        alignment_offset: updateRequest.alignment_offset !== undefined ? updateRequest.alignment_offset : book.alignment_offset,
      };
      updateBook(updatedBook);

      // Close modal after a short delay to show success message
      setTimeout(() => {
        closeModal(EDIT_BOOK_MODAL_KEY);
      }, 1000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update book information');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    // Reset form to original values
    if (book) {
      setTitle(book.book_name || '');
      setAuthor(book.book_author || '');
      setKeywords(book.book_keywords || '');
      setAlignmentOffset(book.alignment_offset?.toString() || '');
    }
    setError(null);
    setSuccess(null);
    closeModal(EDIT_BOOK_MODAL_KEY);
  };

  const handleVisualAlign = () => {
    if (book) {
      openForVisualAlignment(book);
    }
  };

  const modalTitle = book
    ? isNewBook
      ? `New Book: ${book.book_name || `Book ${book.book_id}`}`
      : `Edit Book: ${book.book_name || `Book ${book.book_id}`}`
    : 'Edit Book';

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleCancel}
      title={modalTitle}
      footer={
        <>
          <Button variant="secondary" onClick={handleCancel} disabled={loading}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleSave} isLoading={loading}>
            Save Changes
          </Button>
        </>
      }
    >
      <div className="flex flex-col gap-6">
        {error && (
          <Alert variant="error" onClose={() => setError(null)}>
            {error}
          </Alert>
        )}
        {success && (
          <Alert variant="success" onClose={() => setSuccess(null)}>
            {success}
          </Alert>
        )}

        <div className="flex flex-col gap-4">
          <Input
            label="Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Enter book title"
            disabled={loading}
          />

          <Input
            label="Author"
            value={author}
            onChange={(e) => setAuthor(e.target.value)}
            placeholder="Enter book author"
            disabled={loading}
          />

          <Input
            label="Keywords"
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
            placeholder="Enter keywords (comma-separated)"
            disabled={loading}
          />

          <div className="flex flex-col gap-2">
            <label className="font-medium text-text-primary text-sm">Alignment Offset</label>
            <div className="flex gap-2 items-center justify-between">
              <Button
                variant="primary"
                size="medium"
                onClick={handleVisualAlign}
                disabled={loading || !book}
              >
                Visual Align
              </Button>
              <Input
                type="number"
                value={alignmentOffset}
                onChange={(e) => {
                  // try get first chapter start page number with api
                  setAlignmentOffset(e.target.value);
                }}
                placeholder="Manually set e.g. 10"
                disabled={loading}
                className="flex-1"
              />
            </div>
            <p className="text-sm text-text-secondary mt-[-0.5rem]">
              Alignment offset for page number correction, 
            </p>
            <p className="text-sm text-text-secondary mt-[-0.5rem]">
              (use <b>Visual Align</b> to easily set the offset)
            </p>
          </div>
        </div>
      </div>
    </Modal>
  );
}

