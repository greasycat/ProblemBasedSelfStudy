import { useEffect } from 'react';
import type { ReactNode } from 'react';
import { Button } from './Button';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  footer?: ReactNode;
  maxWidth?: string;
  hideHeader?: boolean;
  noShadow?: boolean;
  zIndex?: number;
}

export function Modal({ isOpen, onClose, title, children, footer, maxWidth = 'max-w-2xl', hideHeader = false, noShadow = false, zIndex = 1000 }: ModalProps) {
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

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0  flex items-center justify-center p-4"
      style={{ zIndex }}
      onClick={onClose}
    >
      <div 
        className={`bg-white rounded-xl border-2  ${maxWidth} w-full max-h-[90vh] flex flex-col ${noShadow ? '' : 'shadow-2xl'} ${hideHeader ? 'relative' : ''}`}
        onClick={(e) => e.stopPropagation()}
      >
        {!hideHeader && (
          <div className="px-6 py-4 shadow-sm flex justify-between items-center rounded-t-xl">
            <h2 className="m-0 text-text-primary text-2xl font-semibold">{title}</h2>
            <Button variant="ghost" size="small" onClick={onClose}>
              ×
            </Button>
          </div>
        )}
        {hideHeader && (
          <div className="absolute top-2 right-2 z-10">
            <Button variant="ghost" size="small" onClick={onClose}>
              ×
            </Button>
          </div>
        )}
        <div className={`${hideHeader ? '' : 'p-6'} overflow-y-auto flex-1 bg-white rounded-b-xl`}>{children}</div>
        {footer && (
          <div className="px-6 py-4 shadow-lg flex justify-end gap-4 bg-background-off">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}
