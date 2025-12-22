import type { ReactNode } from 'react';

interface AlertProps {
  variant?: 'success' | 'error' | 'warning' | 'info';
  children: ReactNode;
  onClose?: () => void;
}

const variantClasses = {
  success: 'bg-green-50 text-success border-green-200',
  error: 'bg-red-50 text-error border-red-200',
  warning: 'bg-yellow-50 text-warning border-yellow-200',
  info: 'bg-blue-50 text-blue-600 border-blue-200',
};

export function Alert({ variant = 'info', children, onClose }: AlertProps) {
  return (
    <div className={`px-6 py-4 rounded-lg flex items-center justify-between gap-4 border ${variantClasses[variant]}`}>
      <div className="flex-1">{children}</div>
      {onClose && (
        <button
          className="bg-transparent border-none text-xl cursor-pointer opacity-70 hover:opacity-100 p-0 w-6 h-6 flex items-center justify-center"
          onClick={onClose}
        >
          ×
        </button>
      )}
    </div>
  );
}
