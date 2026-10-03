import React from 'react';

export interface AlertBannerProps {
  type?: 'info' | 'warning' | 'danger' | 'success';
  title?: string;
  message: string;
  onDismiss?: () => void;
}

export const AlertBanner: React.FC<AlertBannerProps> = ({
  type = 'info',
  title,
  message,
  onDismiss,
}) => {
  return (
    <div className={`alert-banner alert-${type}`} role="alert">
      <div className="alert-content">
        {title && <strong className="alert-title">{title}</strong>}
        <p className="alert-message">{message}</p>
      </div>
      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          className="alert-dismiss-btn"
          aria-label="Dismiss alert"
        >
          ×
        </button>
      )}
    </div>
  );
};
