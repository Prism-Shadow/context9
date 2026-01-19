import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  onValueChange?: (value: string) => void; // Use different name to avoid conflict with react-hook-form
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(({
  label,
  error,
  onValueChange,
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
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
        </label>
      )}
      <input
        {...props}
        ref={ref}
        onChange={handleChange}
        className={`
          w-full px-3 py-2 border rounded-lg shadow-sm
          focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500
          ${error ? 'border-red-500' : 'border-gray-300'}
          ${className}
        `}
      />
      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}
    </div>
  );
});

Input.displayName = 'Input';
