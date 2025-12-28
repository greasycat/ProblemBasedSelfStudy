import { create } from 'zustand';
import { bookApi, sectionApi } from '../services/api';
import { useUIStore } from './useUIStore';
import { useBooksStore } from './useBooksStore';
import type { TocItem } from '../types/api';

interface TocState {
  /** Currently displayed TOC items (chapters or sections) */
  displayItems: TocItem[];
  /** Currently selected TOC item */
  selectedItem: TocItem | null;
  /** Parent item for navigation (used for back button) */
  parentItem: TocItem | null;
  /** Opacity for TOC transition animations */
  opacity: number;
  /** Total pages for the current book */
  totalPages: number | undefined;
}

interface TocStore {
  state: TocState;
  
  // Actions
  /** Set display items */
  setDisplayItems: (items: TocItem[]) => void;
  /** Set selected item */
  setSelectedItem: (item: TocItem | null) => void;
  /** Set parent item */
  setParentItem: (item: TocItem | null) => void;
  /** Set opacity */
  setOpacity: (opacity: number) => void;
  /** Set total pages */
  setTotalPages: (pages: number | undefined) => void;
  /** Reset TOC state */
  reset: () => void;
  
  // Async operations
  /** Fetch chapters for the selected book (uses selectedBook from useBooksStore) */
  fetchChapters: () => Promise<void>;
  /** Fetch sections for a chapter (uses selectedBook from useBooksStore) */
  fetchSections: (chapterId: number) => Promise<void>;
  /** Fetch total pages for the selected book (uses selectedBook from useBooksStore) */
  fetchTotalPages: () => Promise<void>;
  /** Handle TOC item click - selects item and fetches sections if chapter (uses selectedBook from useBooksStore) */
  handleTocItemClick: (item: TocItem) => Promise<void>;
  /** Handle back button navigation (uses selectedBook from useBooksStore) */
  handleBack: () => Promise<void>;
}

const INITIAL_STATE: TocState = {
  displayItems: [],
  selectedItem: null,
  parentItem: null,
  opacity: 1,
  totalPages: undefined,
};

/**
 * Zustand store for managing Table of Contents state
 * Handles chapters, sections, navigation, and animations
 * 
 * Automatically uses the selectedBook from useBooksStore, so no bookId parameter needed.
 * 
 * @example
 * ```tsx
 * const { state, fetchChapters, setSelectedItem, fetchSections, handleTocItemClick } = useTocStore();
 * 
 * // Fetch chapters (uses selectedBook from useBooksStore)
 * await fetchChapters();
 * 
 * // Select an item
 * setSelectedItem(item);
 * 
 * // Fetch sections for a chapter (uses selectedBook from useBooksStore)
 * await fetchSections(chapterId);
 * 
 * // Handle TOC item click (automatically fetches sections if needed)
 * await handleTocItemClick(item);
 * ```
 */
export const useTocStore = create<TocStore>((set, get) => {
  const getUIStore = () => useUIStore.getState();
  const getBooksStore = () => useBooksStore.getState();

  return {
    state: { ...INITIAL_STATE },

    setDisplayItems: (items) => {
      set((state) => ({
        state: {
          ...state.state,
          displayItems: items,
        },
      }));
    },

    setSelectedItem: (item) => {
      set((state) => ({
        state: {
          ...state.state,
          selectedItem: item,
        },
      }));
    },

    setParentItem: (item) => {
      set((state) => ({
        state: {
          ...state.state,
          parentItem: item,
        },
      }));
    },

    setOpacity: (opacity) => {
      set((state) => ({
        state: {
          ...state.state,
          opacity,
        },
      }));
    },

    setTotalPages: (pages) => {
      set((state) => ({
        state: {
          ...state.state,
          totalPages: pages,
        },
      }));
    },

    reset: () => {
      set({ state: { ...INITIAL_STATE } });
    },

    fetchChapters: async () => {
      const store = get();
      const { setLoading } = getUIStore();
      const { selectedBook } = getBooksStore();

      if (!selectedBook?.book_id) {
        store.reset();
        return;
      }

      // Fade out
      store.setOpacity(0);

      setLoading(true);
      try {
        const response = await bookApi.getChapters(selectedBook.book_id);
        store.setDisplayItems(response.chapters);
        store.setSelectedItem(null);
      } catch (error) {
        console.error('Failed to fetch chapters:', error);
        store.setDisplayItems([]);
        store.setSelectedItem(null);
      } finally {
        setLoading(false);
      }

      // Fade in after a delay
      setTimeout(() => {
        get().setOpacity(1);
      }, 200);
    },

    fetchSections: async (chapterId: number) => {
      const store = get();
      const { setLoading } = getUIStore();
      const { selectedBook } = getBooksStore();

      if (!selectedBook?.book_id) return;

      // Fade out
      store.setOpacity(0);

      setLoading(true);
      try {
        const response = await sectionApi.getSections(selectedBook.book_id, chapterId);
        store.setDisplayItems(response.sections);
      } catch (error) {
        console.error('Failed to fetch sections:', error);
        store.setDisplayItems([]);
      } finally {
        setLoading(false);
      }

      // Fade in after a delay
      setTimeout(() => {
        get().setOpacity(1);
      }, 200);
    },

    fetchTotalPages: async () => {
      const store = get();
      const { selectedBook } = getBooksStore();

      if (!selectedBook?.book_id) {
        store.setTotalPages(undefined);
        return;
      }

      try {
        const response = await bookApi.getTotalPages(selectedBook.book_id);
        store.setTotalPages(response.total_pages);
      } catch (error) {
        console.error('Failed to fetch total pages:', error);
        store.setTotalPages(undefined);
      }
    },

    handleTocItemClick: async (item: TocItem) => {
      const store = get();

      if (!item) return;

      // Set parent item if we have a selected item
      if (store.state.selectedItem) {
        store.setParentItem(store.state.selectedItem);
      }

      // Set selected item
      store.setSelectedItem(item);

      // Fetch sections if it's a chapter
      if (item.type === 'chapter' && item.chapter_id) {
        await store.fetchSections(item.chapter_id);
      }
    },

    handleBack: async () => {
      const store = get();

      if (store.state.selectedItem?.type === 'chapter') {
        await store.fetchChapters();
      } else if (store.state.selectedItem?.type === 'section') {
        // Go back to parent item (which should be a chapter)
        store.setSelectedItem(store.state.parentItem);
      }
    },
  };
});

