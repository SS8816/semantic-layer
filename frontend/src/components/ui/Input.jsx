import React from 'react';

const Input = ({
  label,
  error,
  icon,
  className = '',
  ...props
}) => {
  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          {label}
        </label>
      )}
      <div className="relative">
        {icon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            {icon}
          </div>
        )}
        <input
          className={`
            w-full rounded-lg border border-gray-300 dark:border-gray-600
            bg-white dark:bg-gray-800
            text-gray-900 dark:text-gray-100
            placeholder:text-gray-400 dark:placeholder:text-gray-500
            focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
            disabled:opacity-50 disabled:cursor-not-allowed
            ${icon ? 'pl-10' : 'pl-3'}
            pr-3 py-2 text-sm
            ${error ? 'border-red-500 focus:ring-red-500' : ''}
            ${className}
          `}
          {...props}
        />
      </div>
      {error && (
        <p className="mt-1 text-sm text-red-600 dark:text-red-400">{error}</p>
      )}
    </div>
  );
};

export default Input;
