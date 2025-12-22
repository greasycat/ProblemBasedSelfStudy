import type { Book } from '../types/api';
import { Card } from './Card';
import { Button } from './Button';

interface BookCardProps {
  book: Book;
  onView: (book: Book) => void;
  onEdit: (book: Book) => void;
  onDelete: (book: Book) => void;
}

export function BookCard({ book, onView, onEdit, onDelete }: BookCardProps) {
  const fileName = book.pdf_path.split('/').pop() || book.pdf_path;
  const displayName = book.book_name || fileName;

  return (
    <Card className="flex flex-col h-full">
      <div className="flex flex-col gap-4 flex-1">
        {/* Book Title */}
        <div>
          <h4 className="m-0 text-text-primary text-lg font-semibold break-words">{displayName}</h4>
          {book.book_author && (
            <p className="m-0 mt-1 text-sm text-text-secondary">by {book.book_author}</p>
          )}
        </div>

        {/* Book Summary */}
        {book.book_summary && (
          <p className="text-sm text-text-secondary line-clamp-3">{book.book_summary}</p>
        )}

        {/* Keywords */}
        {book.book_keywords && (
          <div className="flex flex-wrap gap-1">
            {book.book_keywords.split(',').map((keyword, idx) => (
              <span
                key={idx}
                className="text-xs px-2 py-1 bg-background-subtle text-text-secondary rounded"
              >
                {keyword.trim()}
              </span>
            ))}
          </div>
        )}

        {/* Book Metadata */}
        <div className="flex gap-6 flex-wrap">
          {book.total_pages !== undefined && (
            <div className="flex flex-col gap-1">
              <span className="text-sm text-text-secondary font-medium">Pages:</span>
              <span className="text-base text-text-primary font-semibold">{book.total_pages}</span>
            </div>
          )}
          <div className="flex flex-col gap-1">
            <span className="text-sm text-text-secondary font-medium">TOC:</span>
            <span className={`text-base font-semibold ${book.toc_exists ? 'text-success' : 'text-error'}`}>
              {book.toc_exists ? 'Yes' : 'No'}
            </span>
          </div>
          {book.book_toc_end_page !== undefined && (
            <div className="flex flex-col gap-1">
              <span className="text-sm text-text-secondary font-medium">TOC End:</span>
              <span className="text-base text-text-primary font-semibold">Page {book.book_toc_end_page}</span>
            </div>
          )}
          {book.alignment_offset !== undefined && book.alignment_offset !== 0 && (
            <div className="flex flex-col gap-1">
              <span className="text-sm text-text-secondary font-medium">Offset:</span>
              <span className="text-base text-text-primary font-semibold">{book.alignment_offset}</span>
            </div>
          )}
        </div>

        {/* File Path */}
        <div className="text-xs text-text-secondary font-mono break-all p-2 bg-background-subtle rounded shadow-sm">
          {book.pdf_path}
        </div>
      </div>
      <div className="flex gap-2 pt-4 shadow-sm flex-wrap">
        <Button variant="primary" size="small" onClick={() => onView(book)} className="flex-1 min-w-[80px]">
          View
        </Button>
        <Button variant="ghost" size="small" onClick={() => onEdit(book)} className="flex-1 min-w-[80px]">
          Edit
        </Button>
        <Button variant="danger" size="small" onClick={() => onDelete(book)} className="flex-1 min-w-[80px]">
          Delete
        </Button>
      </div>
    </Card>
  );
}
