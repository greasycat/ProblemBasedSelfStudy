import { useToastStore } from '../stores/useToastStore';
import { Toast } from './Toast';

/**
 * Global toast container component
 * Renders all active toasts in a fixed position (top-right)
 * Should be added once to the root App component
 */
export function ToastContainer() {
  const toasts = useToastStore((state) => state.toasts);
  const removeToast = useToastStore((state) => state.removeToast);

  if (toasts.length === 0) return null;

  return (
    <div
      className="fixed top-4 right-[3%] translate-y-1/2 z-[9999] flex flex-col gap-3 pointer-events-none"
      aria-live="polite"
      aria-label="Notifications"
    >
      {toasts.map((toast) => (
        <div key={toast.id} className="pointer-events-auto">
          <Toast toast={toast} onClose={() => removeToast(toast.id)} />
        </div>
      ))}
    </div>
  );
}
