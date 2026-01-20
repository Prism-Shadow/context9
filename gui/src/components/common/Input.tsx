import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  onValueChange?: (value: string) => void; // Use different name to avoid conflict with react-hook-form
  endAdornment?: React.ReactNode;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(({
  label,
  error,
  onValueChange,
  endAdornment,
  className = '',
  onChange,
  ...props
}, ref) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    // Call react-hook-form's onChange first (from register)
    if (onChange) {
      onChange(e);
    }
    // If custom onValueChange is provided (for controlled components), call it with value
    if (onValueChange) {
      onValueChange(e.target.value);
    }
  };

  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          {label}
        </label>
      )}
      <div className="relative">
        <input
          {...props}
          ref={ref}
          onChange={handleChange}
          className={`
            w-full px-3 py-2 border rounded-lg shadow-sm
            bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
            focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500
            ${error ? 'border-red-500 dark:border-red-500' : 'border-gray-300 dark:border-gray-600'}
            ${endAdornment ? 'pr-10' : ''}
            ${className}
          `}
        />
        {endAdornment && (
          <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center">
            {endAdornment}
          </div>
        )}
      </div>
      {error && (
        <p className="mt-1 text-sm text-red-600 dark:text-red-400">{error}</p>
      )}
    </div>
  );
});

Input.displayName = 'Input';
