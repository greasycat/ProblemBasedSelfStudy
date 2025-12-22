import type { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  title?: string;
  className?: string;
  actions?: ReactNode;
}

export function Card({ children, title, className = '', actions }: CardProps) {
  return (
    <div className={`bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow duration-200 overflow-hidden ${className}`}>
      {(title || actions) && (
        <div className="px-6 py-4 shadow-sm flex justify-between items-center bg-background-off">
          {title && <h3 className="m-0 text-text-primary text-xl font-semibold">{title}</h3>}
          {actions && <div className="flex gap-2">{actions}</div>}
        </div>
      )}
      <div className="p-6">{children}</div>
    </div>
  );
}
