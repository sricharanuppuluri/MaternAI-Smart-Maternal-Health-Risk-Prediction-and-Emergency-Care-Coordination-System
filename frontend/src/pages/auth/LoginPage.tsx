import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../../auth';
import { Input, Button, AlertBanner } from '../../components/common';
import type { UserRole } from '../../types/auth';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [role, setRole] = useState<UserRole>('MOTHER');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Return to intended destination or portal home
  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || (role === 'ASHA' ? '/asha' : '/mother');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await login(role, email || undefined);
      navigate(from, { replace: true });
    } catch {
      setError('Unable to authenticate. Please check your credentials.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-form-card" role="region" aria-labelledby="login-heading">
      <h2 id="login-heading" className="auth-heading">Sign In to MaternAI</h2>
      <p className="auth-instructions">Select your care role and sign in to access your portal</p>

      {error && <AlertBanner type="danger" message={error} onDismiss={() => setError(null)} />}

      <form onSubmit={handleSubmit} className="auth-form" noValidate>
        {/* Role Selection Tabs */}
        <div className="role-selector-group" role="radiogroup" aria-label="Care Role">
          <label className="input-label">I am signing in as:</label>
          <div className="role-toggle-buttons">
            <button
              type="button"
              role="radio"
              aria-checked={role === 'MOTHER'}
              className={`role-toggle-btn ${role === 'MOTHER' ? 'active' : ''}`}
              onClick={() => setRole('MOTHER')}
            >
              👩 Expecting / New Mother
            </button>
            <button
              type="button"
              role="radio"
              aria-checked={role === 'ASHA'}
              className={`role-toggle-btn ${role === 'ASHA' ? 'active' : ''}`}
              onClick={() => setRole('ASHA')}
            >
              🩺 ASHA Health Worker
            </button>
          </div>
        </div>

        <Input
          id="login-email"
          type="email"
          label="Email Address or Mobile Identifier"
          placeholder={role === 'MOTHER' ? 'mother@maternai.org' : 'asha.worker@maternai.org'}
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          helperText="Phase 1 development: Enter any demo identifier or leave default"
        />

        <Input
          id="login-password"
          type="password"
          label="Password"
          placeholder="••••••••"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          helperText="Phase 1 uses client session mock; Supabase Auth integrates in Phase 3"
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

      <div className="auth-footer-links">
        <span>Don't have an account yet? </span>
        <Link to="/auth/register" className="auth-link">
          Register here
        </Link>
      </div>
    </div>
  );
};
