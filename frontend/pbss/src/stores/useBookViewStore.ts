import { create } from 'zustand';
import { bookApi } from '../services/api';
import type { Book } from '../types/api';

interface BookViewState {
  /** Whether the book view is currently open */
  isOpen: boolean;
  /** The book being viewed */
  book: Book | null;
  /** The current page number */
  currentPage: number;
}

interface BookViewStore {
  state: BookViewState;
  
  // Actions
  open: (book: Book) => void;
  close: () => void;
  setPage: (page: number) => void;
  openForVisualAlignment: (book: Book) => Promise<void>;
}

export const useBookViewStore = create<BookViewStore>((set) => ({
  state: {
    isOpen: false,
    book: null,
    currentPage: 0,
  },

  open: (book: Book) => {
    set({
      state: {
        isOpen: true,
        book,
        currentPage: 0,
      },
    });
  },

  close: () => {
    set({
      state: {
        isOpen: false,
        book: null,
        currentPage: 0,
      },
    });
  },

  setPage: (page: number) => {
    set((state) => ({
      state: {
        ...state.state,
        currentPage: page,
      },
    }));
  },

  openForVisualAlignment: async (book: Book) => {
    // Start at page 0 or use alignment offset if it exists
    let initialPage = book.alignment_offset || 0;
    
    set({
      state: {
        isOpen: true,
        book,
        currentPage: initialPage,
      },
    });

    // Try to fetch chapters and set page to first chapter start page
    try {
      const response = await bookApi.getChapters(book.book_id || 0);
      const chapters = response.chapters;
      if (chapters.length > 0) {
        const firstChapterStartPageNumber = chapters[0].start_page_number;
        initialPage = firstChapterStartPageNumber + (book.alignment_offset || 0);
        set((state) => ({
          state: {
            ...state.state,
            currentPage: initialPage,
          },
        }));
      } else {
        // No chapters found, keep page at 0
        set((state) => ({
          state: {
            ...state.state,
            currentPage: 0,
          },
        }));
      }
    } catch (error) {
      // Failed to get chapters, keep page at alignment offset or 0
      set((state) => ({
        state: {
          ...state.state,
          currentPage: book.alignment_offset || 0,
        },
      }));
    }
  },
}));

