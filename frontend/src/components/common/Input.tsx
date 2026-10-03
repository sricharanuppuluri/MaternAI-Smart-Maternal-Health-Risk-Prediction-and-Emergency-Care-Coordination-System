import React from 'react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  id: string;
  error?: string;
  helperText?: string;
}

export const Input: React.FC<InputProps> = ({
  label,
  id,
  error,
  helperText,
  className = '',
  required,
  ...props
}) => {
  return (
    <div className={`input-field-group ${error ? 'has-error' : ''} ${className}`}>
      <label htmlFor={id} className="input-label">
        {label}
        {required && <span className="required-asterisk" aria-hidden="true">*</span>}
      </label>
      <input
        id={id}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? `${id}-error` : helperText ? `${id}-helper` : undefined}
        required={required}
        className="input-control"
        {...props}
      />
      {error && (
        <p id={`${id}-error`} className="input-error" role="alert">
          {error}
        </p>
      )}
      {helperText && !error && (
        <p id={`${id}-helper`} className="input-helper">
          {helperText}
        </p>
      )}
    </div>
  );
};
