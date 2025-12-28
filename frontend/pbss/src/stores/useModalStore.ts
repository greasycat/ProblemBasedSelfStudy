import { create } from 'zustand';

export interface ModalState<T = unknown> {
  isOpen: boolean;
  data: T | null;
}

// Stable default modal state to prevent infinite loops
export const DEFAULT_MODAL_STATE: ModalState = {
  isOpen: false,
  data: null,
};

interface ModalStore {
  // Modal states by key
  modals: Record<string, ModalState>;
  
  // Actions
  openModal: <T>(key: string, data?: T) => void;
  closeModal: (key: string) => void;
}

/**
 * Zustand store for managing modal states
 * Supports multiple modals identified by string keys
 * 
 * Use selectors to access modal state reactively:
 * 
 * @example
 * ```tsx
 * // Get actions
 * const { openModal, closeModal } = useModalStore();
 * 
 * // Get modal state reactively using selector
 * const editModalState = useModalStore((state) => 
 *   state.modals['editBook'] || { isOpen: false, data: null }
 * );
 * 
 * // Open a modal
 * openModal('editBook', book);
 * 
 * // Close modal
 * closeModal('editBook');
 * 
 * // Check if open and get data
 * if (editModalState.isOpen) {
 *   const book = editModalState.data;
 * }
 * ```
 */
export const useModalStore = create<ModalStore>((set) => ({
  modals: {},

  openModal: <T,>(key: string, data?: T) => {
    set((state) => ({
      modals: {
        ...state.modals,
        [key]: {
          isOpen: true,
          data: data ?? null,
        },
      },
    }));
  },

  closeModal: (key: string) => {
    set((state) => {
      const newModals = { ...state.modals };
      // Always maintain the modal entry to ensure stable references
      newModals[key] = {
        isOpen: false,
        data: null,
      };
      return { modals: newModals };
    });
  },
}));

