import type { ButtonHTMLAttributes, ReactNode } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'small' | 'medium' | 'large' | 'full';
  children: ReactNode;
  isLoading?: boolean;
}

const variantClasses = {
  primary: 'bg-primary text-white hover:bg-primary-dark hover:shadow-lg shadow-primary/20',
  secondary: 'bg-primary-light text-white hover:bg-primary hover:shadow-lg shadow-primary/20',
  danger: 'bg-error text-white hover:bg-red-600 hover:shadow-lg shadow-error/20',
  ghost: 'bg-transparent text-text-primary hover:bg-background-subtle',
};

const sizeClasses = {
  small: 'px-4 py-2 text-sm',
  medium: 'px-6 py-3 text-base',
  large: 'px-8 py-4 text-lg',
  full: 'w-full h-12',
};

export function Button({
  variant = 'primary',
  size = 'medium',
  children,
  isLoading = false,
  disabled,
  className = '',
  ...props
}: ButtonProps) {
  const baseClasses = 'inline-flex items-center justify-center gap-2 rounded-lg cursor-pointer transition-all duration-200 disabled:opacity-60 disabled:cursor-not-allowed';
  const variantClass = variantClasses[variant];
  const sizeClass = sizeClasses[size];
  const loadingClass = isLoading ? 'relative text-transparent' : '';

  return (
    <button
      className={`${baseClasses} ${variantClass} ${sizeClass} ${loadingClass} ${className}`.trim()}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <>
          <span className="inline-block w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <span className="text-primary font-bold"> Uploading... </span>
        </>
      ) : (
        children
      )}
    </button>
  );
}
