import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../auth';
import { Input, Button, AlertBanner } from '../../components/common';
import type { UserRole } from '../../types/auth';
import { isValidEmail } from '../../utils/validation';

export const RegisterPage: React.FC = () => {
  const { signUp, error: authError, clearError } = useAuth();
  const navigate = useNavigate();

  const [role, setRole] = useState<UserRole>('MOTHER');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [phone, setPhone] = useState('');
  const [fieldErrors, setFieldErrors] = useState<{
    fullName?: string;
    email?: string;
    password?: string;
  }>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const validateForm = (): boolean => {
    const errors: { fullName?: string; email?: string; password?: string } = {};

    if (!fullName.trim()) {
      errors.fullName = 'Full legal name is required';
    }

    if (!email.trim()) {
      errors.email = 'Email address is required';
    } else if (!isValidEmail(email)) {
      errors.email = 'Please provide a valid email address';
    }

    if (password && password.length < 6) {
      errors.password = 'Password must be at least 6 characters long';
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    clearError();

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      await signUp({
        email: email.trim(),
        password: password || undefined,
        full_name: fullName.trim(),
        role,
        phone: phone.trim() || undefined,
      });
      navigate(role === 'ASHA' ? '/asha' : '/mother', { replace: true });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Registration failed. Please try again.';
      setLocalError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const activeError = localError || authError;

  return (
    <div className="auth-form-card" role="region" aria-labelledby="register-heading">
      <h2 id="register-heading" className="auth-heading">Create MaternAI Account</h2>
      <p className="auth-instructions">Join the secure maternal health coordination network</p>

      {activeError && (
        <AlertBanner
          type="danger"
          message={activeError}
          onDismiss={() => {
            setLocalError(null);
            clearError();
          }}
        />
      )}

      <form onSubmit={handleSubmit} className="auth-form" noValidate>
        {/* Role Selector */}
        <div className="role-selector-group" role="radiogroup" aria-label="Registration Role">
          <label className="input-label">Account Role:</label>
          <div className="role-toggle-buttons">
            <button
              type="button"
              role="radio"
              aria-checked={role === 'MOTHER'}
              className={`role-toggle-btn ${role === 'MOTHER' ? 'active' : ''}`}
              onClick={() => setRole('MOTHER')}
            >
              👩 Mother Account
            </button>
            <button
              type="button"
              role="radio"
              aria-checked={role === 'ASHA'}
              className={`role-toggle-btn ${role === 'ASHA' ? 'active' : ''}`}
              onClick={() => setRole('ASHA')}
            >
              🩺 ASHA Worker Account
            </button>
          </div>
          <p className="input-helper mt-1">
            Note: System Administrator (ADMIN) access requires server-controlled provisioning.
          </p>
        </div>

        <Input
          id="reg-name"
          type="text"
          label="Full Legal Name"
          placeholder="e.g. Priya Sharma"
          value={fullName}
          onChange={(e) => {
            setFullName(e.target.value);
            if (fieldErrors.fullName) setFieldErrors({ ...fieldErrors, fullName: undefined });
          }}
          error={fieldErrors.fullName}
          required
          autoComplete="name"
        />

        <Input
          id="reg-email"
          type="email"
          label="Email Address"
          placeholder="name@example.com"
          value={email}
          onChange={(e) => {
            setEmail(e.target.value);
            if (fieldErrors.email) setFieldErrors({ ...fieldErrors, email: undefined });
          }}
          error={fieldErrors.email}
          required
          autoComplete="email"
        />

        <Input
          id="reg-password"
          type="password"
          label="Account Password"
          placeholder="At least 6 characters"
          value={password}
          onChange={(e) => {
            setPassword(e.target.value);
            if (fieldErrors.password) setFieldErrors({ ...fieldErrors, password: undefined });
          }}
          error={fieldErrors.password}
          autoComplete="new-password"
          helperText="Required for Supabase Auth account creation"
        />

        <Input
          id="reg-phone"
          type="tel"
          label="Mobile Phone (+91, Optional)"
          placeholder="+91 9876543210"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          autoComplete="tel"
        />

        <Button
          type="submit"
          variant="primary"
          className="w-full mt-4"
          isLoading={isSubmitting}
        >
          Register & Create Profile
        </Button>
      </form>

      <div className="auth-footer-links">
        <span>Already have an account? </span>
        <Link to="/auth/login" className="auth-link">
          Sign in
        </Link>
      </div>
    </div>
  );
};
