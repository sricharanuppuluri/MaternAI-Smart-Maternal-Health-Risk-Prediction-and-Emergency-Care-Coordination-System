import React from 'react';

export interface BadgeProps {
  label: string;
  variant?: 'success' | 'warning' | 'danger' | 'info' | 'critical' | 'neutral';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  label,
  variant = 'neutral',
  className = '',
}) => {
  return (
    <span className={`badge badge-${variant} ${className}`}>
      {label}
    </span>
  );
};
