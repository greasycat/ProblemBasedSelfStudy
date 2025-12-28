import { create } from 'zustand';

export type ToastType = 'info' | 'success' | 'error' | 'warning';

export interface Toast {
  id: string;
  message: string;
  type: ToastType;
  duration?: number; // Auto-dismiss duration in ms, undefined means no auto-dismiss
}

interface ToastStore {
  toasts: Toast[];
  
  // Actions
  showToast: (message: string, type?: ToastType, duration?: number) => string;
  removeToast: (id: string) => void;
  clearToasts: () => void;
}

/**
 * Zustand store for managing global toast notifications
 * 
 * @example
 * ```tsx
 * const { showToast, removeToast } = useToastStore();
 * 
 * // Show a success toast (auto-dismisses after 5 seconds)
 * showToast('Operation successful!', 'success');
 * 
 * // Show an error toast (auto-dismisses after 5 seconds)
 * showToast('Something went wrong', 'error');
 * 
 * // Show an info toast with custom duration
 * showToast('Processing...', 'info', 3000);
 * 
 * // Show a toast that doesn't auto-dismiss
 * const toastId = showToast('Please wait...', 'info', 0);
 * // Later, manually dismiss it
 * removeToast(toastId);
 * ```
 */
export const useToastStore = create<ToastStore>((set) => ({
  toasts: [],

  showToast: (message, type = 'info', duration = 5000) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const toast: Toast = { id, message, type, duration };
    
    set((state) => ({
      toasts: [...state.toasts, toast],
    }));

    // Auto-dismiss if duration is set and greater than 0
    if (duration > 0) {
      setTimeout(() => {
        set((state) => ({
          toasts: state.toasts.filter((t) => t.id !== id),
        }));
      }, duration);
    }

    return id;
  },

  removeToast: (id) => {
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    }));
  },

  clearToasts: () => {
    set({ toasts: [] });
  },
}));
