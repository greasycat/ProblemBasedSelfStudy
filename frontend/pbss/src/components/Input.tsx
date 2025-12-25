import { forwardRef } from 'react';
import type { InputHTMLAttributes } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className = '', ...props }, ref) => {
    return (
      <div className="flex flex-col gap-2">
        {label && (
          <label className="font-medium text-text-primary text-sm" htmlFor={props.id}>
            {label}
          </label>
        )}
        <input
          ref={ref}
          className={`
            px-4 py-3 border-2 border-gray-200 rounded-lg text-base font-inherit transition-colors duration-200
            bg-white text-text-primary
            ${error 
              ? 'border-error focus:border-error' 
              : 'border-border focus:border-primary focus:outline-none'
            }
            ${className}
          `.trim()}
          {...props}
        />
        {error && <span className="text-error text-sm">{error}</span>}
      </div>
    );
  }
);

Input.displayName = 'Input';
