import React from 'react';

const Badge = ({ children, variant = 'default', size = 'md', className = '', ...props }) => {
  const baseStyles = 'inline-flex items-center gap-1 font-medium rounded-full';

  const variants = {
    default: 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300',
    primary: 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300',
    success: 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300',
    warning: 'bg-amber-100 dark:bg-amber-900 text-amber-700 dark:text-amber-300',
    danger: 'bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300',
    info: 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300',
    enriched: 'bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300',
    relationships: 'bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300',
    stale: 'bg-orange-100 dark:bg-orange-900 text-orange-700 dark:text-orange-300',
  };

  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-xs',
    lg: 'px-3 py-1.5 text-sm',
  };

  return (
    <span className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`} {...props}>
      {children}
    </span>
  );
};

export default Badge;
