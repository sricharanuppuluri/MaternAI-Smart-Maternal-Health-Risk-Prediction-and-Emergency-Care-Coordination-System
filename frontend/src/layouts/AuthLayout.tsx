import React from 'react';
import { Outlet, Link } from 'react-router-dom';

export const AuthLayout: React.FC = () => {
  return (
    <div className="auth-layout-container">
      <div className="auth-card-wrapper">
        <div className="auth-header">
          <Link to="/" className="auth-brand" aria-label="MaternAI Home">
            <span className="auth-brand-icon" aria-hidden="true">🤱</span>
            <span className="auth-brand-name">Matern<span className="brand-accent">AI</span></span>
          </Link>
          <p className="auth-subtitle">Secure Maternal Health Screening & Care Coordination</p>
        </div>
        <Outlet />
      </div>
    </div>
  );
};
