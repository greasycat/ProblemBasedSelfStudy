import { create } from 'zustand';
import type { Book } from '../types/api';

interface UIState {
  /** Global loading state */
  loading: boolean;
  /** Global error message */
  error: string | null;
  /** Book to view in PDF modal */
  pdfViewBook: Book | null;
  
  // Actions
  /** Set loading state */
  setLoading: (loading: boolean) => void;
  /** Set error message */
  setError: (error: string | null) => void;
  /** Clear error message */
  clearError: () => void;
  /** Set book to view in PDF modal */
  setPdfViewBook: (book: Book | null) => void;
}

/**
 * Zustand store for managing global UI state
 * This store centralizes UI state management (loading, errors) across the application
 * 
 * @example
 * ```tsx
 * const { loading, error, setLoading, setError, clearError } = useUIStore();
 * 
 * // Set loading
 * setLoading(true);
 * 
 * // Set error
 * setError('Something went wrong');
 * 
 * // Clear error
 * clearError();
 * ```
 */
export const useUIStore = create<UIState>((set) => ({
  loading: false,
  error: null,
  pdfViewBook: null,

  setLoading: (loading) => set({ loading }),

  setError: (error) => set({ error }),

  clearError: () => set({ error: null }),

  setPdfViewBook: (book) => set({ pdfViewBook: book }),
}));

