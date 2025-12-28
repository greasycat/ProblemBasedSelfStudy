import { useEffect, useState } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import type { Toast as ToastType } from '../stores/useToastStore';

interface ToastProps {
  toast: ToastType;
  onClose: () => void;
}

const typeClasses = {
  success: 'bg-green-50 text-success border-green-200',
  error: 'bg-red-50 text-error border-red-200',
  warning: 'bg-yellow-50 text-warning border-yellow-200',
  info: 'bg-blue-50 text-blue-800 border-blue-200',
};

const iconClasses = {
  success: 'text-success',
  error: 'text-error',
  warning: 'text-warning',
  info: 'text-blue-600',
};

export function Toast({ toast, onClose }: ToastProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [isExiting, setIsExiting] = useState(false);

  useEffect(() => {
    // Trigger entrance animation
    requestAnimationFrame(() => {
      setIsVisible(true);
    });
  }, []);

  const handleClose = () => {
    setIsExiting(true);
    // Wait for exit animation before removing
    setTimeout(() => {
      onClose();
    }, 300);
  };

  return (
    <div
      className={`
        min-w-[300px] max-w-[500px] rounded-lg border shadow-lg p-4 flex items-start gap-3
        transition-all duration-300 ease-in-out
        ${typeClasses[toast.type]}
        ${isVisible && !isExiting ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-full'}
        ${isExiting ? 'opacity-0 translate-x-full' : ''}
      `}
      role="alert"
    >
      {/* Message */}
      <div className="flex-1 text-sm font-medium">{toast.message}</div>
      
      {/* Close Button */}
      <button
        onClick={handleClose}
        className={`
          flex-shrink-0 p-1 rounded hover:bg-black/10 transition-colors
          ${iconClasses[toast.type]}
        `}
        aria-label="Close toast"
      >
        <XMarkIcon className="w-5 h-5" />
      </button>
    </div>
  );
}
