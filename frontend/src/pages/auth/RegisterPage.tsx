import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../auth';
import { Input, Button, AlertBanner } from '../../components/common';
import type { UserRole } from '../../types/auth';

export const RegisterPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [role, setRole] = useState<UserRole>('MOTHER');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fullName.trim()) {
      setError('Please provide your full name.');
      return;
    }
    setError(null);
    setIsSubmitting(true);

    try {
      await login(role, email || undefined);
      navigate(role === 'ASHA' ? '/asha' : '/mother');
    } catch {
      setError('Registration failed. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-form-card" role="region" aria-labelledby="register-heading">
      <h2 id="register-heading" className="auth-heading">Create MaternAI Account</h2>
      <p className="auth-instructions">Join the maternal care coordination network</p>

      {error && <AlertBanner type="danger" message={error} onDismiss={() => setError(null)} />}

      <form onSubmit={handleSubmit} className="auth-form" noValidate>
        <div className="role-selector-group" role="radiogroup" aria-label="Registration Role">
          <label className="input-label">I want to register as:</label>
          <div className="role-toggle-buttons">
            <button
              type="button"
              role="radio"
              aria-checked={role === 'MOTHER'}
              className={`role-toggle-btn ${role === 'MOTHER' ? 'active' : ''}`}
              onClick={() => setRole('MOTHER')}
            >
              👩 Mother
            </button>
            <button
              type="button"
              role="radio"
              aria-checked={role === 'ASHA'}
              className={`role-toggle-btn ${role === 'ASHA' ? 'active' : ''}`}
              onClick={() => setRole('ASHA')}
            >
              🩺 ASHA Worker
            </button>
          </div>
        </div>

        <Input
          id="reg-name"
          type="text"
          label="Full Legal Name"
          placeholder="e.g. Priya Sharma"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          required
        />

        <Input
          id="reg-email"
          type="email"
          label="Email Address"
          placeholder="name@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        <Input
          id="reg-phone"
          type="tel"
          label="Mobile Phone (+91)"
          placeholder="+91 9876543210"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
        />

        <Button
          type="submit"
          variant="primary"
          className="w-full mt-4"
          isLoading={isSubmitting}
        >
          Complete Registration (Phase 1 Demo)
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
