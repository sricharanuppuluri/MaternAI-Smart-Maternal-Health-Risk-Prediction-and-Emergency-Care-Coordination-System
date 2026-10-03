import React from 'react';

export interface LoadingSpinnerProps {
  label?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  label = 'Loading...',
  size = 'md',
}) => {
  return (
    <div className={`spinner-container spinner-${size}`} role="status">
      <div className="spinner-animation" aria-hidden="true" />
      <span className="sr-only">{label}</span>
    </div>
  );
};
