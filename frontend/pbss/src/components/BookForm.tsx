import { useState } from 'react';
import type { FormEvent } from 'react';
import { Modal } from './Modal';
import { Input } from './Input';
import { Button } from './Button';
import { Alert } from './Alert';
import { bookApi } from '../services/api';
import type { Book } from '../types/api';

interface BookFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (book: Book) => void;
  initialBook?: Book;
}

export function BookForm({ isOpen, onClose, onSubmit, initialBook }: BookFormProps) {
  const [pdfPath, setPdfPath] = useState(initialBook?.pdf_path || '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      // Create/Update book info
      await bookApi.updateBookInfo({
        pdf_path: pdfPath,
        overwrite: false,
      });

      // Load book details
      const [totalPagesResponse, tocResponse] = await Promise.all([
        bookApi.getTotalPages({ pdf_path: pdfPath }),
        bookApi.checkTocExists(pdfPath).catch(() => ({ pdf_path: pdfPath, toc_exists: false })),
      ]);

      const book: Book = {
        pdf_path: pdfPath,
        total_pages: totalPagesResponse.total_pages,
        toc_exists: tocResponse.toc_exists,
      };

      onSubmit(book);
      setPdfPath('');
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create book');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setPdfPath(initialBook?.pdf_path || '');
    setError(null);
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={initialBook ? 'Edit Book' : 'Add New Book'}
      footer={
        <>
          <Button variant="ghost" onClick={handleClose} disabled={loading}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleSubmit} isLoading={loading}>
            {initialBook ? 'Update' : 'Create'}
          </Button>
        </>
      }
    >
      <form onSubmit={handleSubmit}>
        {error && (
          <Alert variant="error" onClose={() => setError(null)}>
            {error}
          </Alert>
        )}
        <div className="mt-4">
          <Input
            label="PDF Path"
            type="text"
            value={pdfPath}
            onChange={(e) => setPdfPath(e.target.value)}
            placeholder="/path/to/your/book.pdf"
            required
            disabled={loading || !!initialBook}
          />
          <p className="text-sm text-text-secondary mt-2">
            Enter the absolute path to the PDF file on the server
          </p>
        </div>
      </form>
    </Modal>
  );
}
