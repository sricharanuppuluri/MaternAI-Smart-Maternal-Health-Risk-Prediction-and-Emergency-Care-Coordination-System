import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../../auth';
import { Input, Button, AlertBanner } from '../../components/common';
import type { UserRole } from '../../types/auth';
import { isValidEmail } from '../../utils/validation';

export const LoginPage: React.FC = () => {
  const { signIn, error: authError, clearError } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [role, setRole] = useState<UserRole>('MOTHER');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fieldErrors, setFieldErrors] = useState<{ email?: string; password?: string }>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  // Return to intended destination or appropriate role portal
  const from =
    (location.state as { from?: { pathname: string } })?.from?.pathname ||
    (role === 'ASHA' ? '/asha' : '/mother');

  const validateForm = (): boolean => {
    const errors: { email?: string; password?: string } = {};

    if (!email.trim()) {
      errors.email = 'Email address or mobile identifier is required';
    } else if (email.includes('@') && !isValidEmail(email)) {
      errors.email = 'Please enter a valid email address';
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
      await signIn({
        email: email.trim(),
        password: password || undefined,
        role,
      });
      navigate(from, { replace: true });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Authentication failed. Please check your credentials.';
      setLocalError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleQuickDemo = async (demoRole: UserRole) => {
    setRole(demoRole);
    setLocalError(null);
    clearError();
    setIsSubmitting(true);

    try {
      await signIn({
        email: `${demoRole.toLowerCase()}@maternai.org`,
        role: demoRole,
      });
      navigate(demoRole === 'ASHA' ? '/asha' : '/mother', { replace: true });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Demo sign in failed';
      setLocalError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const activeError = localError || authError;

  return (
    <div className="auth-form-card" role="region" aria-labelledby="login-heading">
      <h2 id="login-heading" className="auth-heading">Sign In to MaternAI</h2>
      <p className="auth-instructions">Access the secure maternal care coordination portal</p>

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
        {/* Care Role Selection */}
        <div className="role-selector-group" role="radiogroup" aria-label="Care Portal Role">
          <label className="input-label">Signing in as:</label>
          <div className="role-toggle-buttons">
            <button
              type="button"
              role="radio"
              aria-checked={role === 'MOTHER'}
              className={`role-toggle-btn ${role === 'MOTHER' ? 'active' : ''}`}
              onClick={() => {
                setRole('MOTHER');
                setFieldErrors({});
              }}
            >
              👩 Mother Portal
            </button>
            <button
              type="button"
              role="radio"
              aria-checked={role === 'ASHA'}
              className={`role-toggle-btn ${role === 'ASHA' ? 'active' : ''}`}
              onClick={() => {
                setRole('ASHA');
                setFieldErrors({});
              }}
            >
              🩺 ASHA Portal
            </button>
          </div>
        </div>

        <Input
          id="login-email"
          type="email"
          label="Email Address or Mobile Identifier"
          placeholder={role === 'MOTHER' ? 'mother@maternai.org' : 'asha.worker@maternai.org'}
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
          id="login-password"
          type="password"
          label="Password"
          placeholder="••••••••"
          value={password}
          onChange={(e) => {
            setPassword(e.target.value);
            if (fieldErrors.password) setFieldErrors({ ...fieldErrors, password: undefined });
          }}
          error={fieldErrors.password}
          autoComplete="current-password"
          helperText="Enter your Supabase Auth account password"
        />

        <Button
          type="submit"
          variant="primary"
          className="w-full mt-4"
          isLoading={isSubmitting}
        >
          Sign In to {role === 'MOTHER' ? 'Mother Portal' : 'ASHA Portal'}
        </Button>
      </form>

      {/* Demo / Quick Sign-In for offline local development */}
      <div className="demo-login-box mt-4 p-3 border rounded text-center">
        <p className="text-xs text-muted mb-2 font-semibold">Development & Offline Demo Shortcuts:</p>
        <div className="flex gap-2 justify-center">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => handleQuickDemo('MOTHER')}
            disabled={isSubmitting}
          >
            Demo as Mother
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => handleQuickDemo('ASHA')}
            disabled={isSubmitting}
          >
            Demo as ASHA
          </Button>
        </div>
      </div>

      <div className="auth-footer-links">
        <span>Don't have an account yet? </span>
        <Link to="/auth/register" className="auth-link">
          Register here
        </Link>
      </div>
    </div>
  );
};
