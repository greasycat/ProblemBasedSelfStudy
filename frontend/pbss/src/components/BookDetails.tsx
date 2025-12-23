import { useState, useEffect } from 'react';
import { Modal } from './Modal';
import { Button } from './Button';
import { Alert } from './Alert';
import { Card } from './Card';
import { bookApi } from '../services/api';
import type { Book } from '../types/api';

interface BookDetailsProps {
  isOpen: boolean;
  onClose: () => void;
  book: Book | null;
  onUpdate: (book: Book) => void;
}

export function BookDetails({ isOpen, onClose, book, onUpdate }: BookDetailsProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [pageText, setPageText] = useState<string>('');
  const [selectedPage, setSelectedPage] = useState<number>(0);
  const [pageImage, setPageImage] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && book) {
      setSelectedPage(0);
      setPageText('');
      setPageImage(null);
      setError(null);
      setSuccess(null);
    }
  }, [isOpen, book]);

  const handleUpdateBookInfo = async () => {
    if (!book) return;
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      await bookApi.updateBookInfo({
        book_id: book.book_id,
        overwrite: true,
      });
      setSuccess('Book information updated successfully');
      // Reload book details
      const [totalPagesResponse, tocResponse] = await Promise.all([
        bookApi.getTotalPages(book.book_id),
        bookApi.checkTocExists(book.book_id).catch(() => ({ book_id: book.book_id, toc_exists: false })),
      ]);
      onUpdate({
        ...book,
        total_pages: totalPagesResponse.total_pages,
        toc_exists: tocResponse.toc_exists,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update book info');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateToc = async () => {
    if (!book) return;
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      await bookApi.updateToc({
        book_id: book.book_id,
        overwrite: true,
        caching: true,
      });
      setSuccess('Table of contents updated successfully');
      const tocResponse = await bookApi.checkTocExists(book.book_id);
      onUpdate({ ...book, toc_exists: tocResponse.toc_exists });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update TOC');
    } finally {
      setLoading(false);
    }
  };

  const handleLoadPage = async () => {
    if (!book || book.total_pages === undefined) return;
    if (selectedPage < 0 || selectedPage >= book.total_pages) {
      setError('Invalid page number');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const [textResponse, imageResponse] = await Promise.all([
        bookApi.getPageText({ book_id: book.book_id, page_number: selectedPage }),
        bookApi.getPageImage({ book_id: book.book_id, page_number: selectedPage, dpi: 150 }),
      ]);
      setPageText(textResponse.text);
      setPageImage(`data:image/png;base64,${imageResponse.image_base64}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load page');
    } finally {
      setLoading(false);
    }
  };

  if (!book) return null;

  const fileName = book.book_name || `Unknown Book ${book.book_id}`;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Book Details: ${fileName}`}
      footer={
        <Button variant="primary" onClick={onClose}>
          Close
        </Button>
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

        <Card title="Book Information">
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <label className="font-semibold text-text-secondary text-sm">Path:</label>
              <span className="text-text-primary break-all font-mono p-2 bg-background-subtle rounded shadow-sm">{book.book_name}</span>
            </div>
            {book.total_pages !== undefined && (
              <div className="flex flex-col gap-2">
                <label className="font-semibold text-text-secondary text-sm">Total Pages:</label>
                <span className="text-text-primary p-2 bg-background-subtle rounded shadow-sm">{book.total_pages}</span>
              </div>
            )}
            <div className="flex flex-col gap-2">
              <label className="font-semibold text-text-secondary text-sm">Table of Contents:</label>
              <span className={`p-2 bg-background-subtle rounded shadow-sm ${book.toc_exists ? 'text-success' : 'text-error'}`}>
                {book.toc_exists ? 'Available' : 'Not Available'}
              </span>
            </div>
          </div>
          <div className="flex gap-4 mt-4 flex-wrap">
            <Button variant="primary" onClick={handleUpdateBookInfo} isLoading={loading}>
              Update Book Info
            </Button>
            <Button variant="secondary" onClick={handleUpdateToc} isLoading={loading}>
              Update TOC
            </Button>
          </div>
        </Card>

        {book.total_pages !== undefined && (
          <Card title="View Page">
            <div className="flex items-center gap-4 mb-4">
              <input
                type="number"
                min="0"
                max={book.total_pages - 1}
                value={selectedPage}
                onChange={(e) => setSelectedPage(parseInt(e.target.value) || 0)}
                className="px-2 py-2 border-2 border-border rounded w-24 text-base focus:border-primary focus:outline-none bg-white shadow-sm"
              />
              <span className="text-text-secondary">of {book.total_pages - 1}</span>
              <Button variant="primary" onClick={handleLoadPage} isLoading={loading}>
                Load Page
              </Button>
            </div>
            {pageText && (
              <div className="mt-4">
                <h4 className="m-0 mb-2 text-text-primary">Page Text:</h4>
                <pre className="bg-background-subtle p-4 rounded overflow-x-auto max-h-[300px] overflow-y-auto text-sm leading-relaxed shadow-sm">{pageText}</pre>
              </div>
            )}
            {pageImage && (
              <div className="mt-4">
                <h4 className="m-0 mb-2 text-text-primary">Page Image:</h4>
                <img src={pageImage} alt={`Page ${selectedPage}`} className="max-w-full h-auto shadow-md rounded" />
              </div>
            )}
          </Card>
        )}
      </div>
    </Modal>
  );
}
