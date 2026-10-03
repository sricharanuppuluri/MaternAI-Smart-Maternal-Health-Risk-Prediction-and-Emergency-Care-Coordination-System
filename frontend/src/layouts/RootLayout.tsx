import React from 'react';
import { Outlet, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth';

const CURRENT_YEAR = new Date().getFullYear();

export const RootLayout: React.FC = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <div className="app-shell">
      <a href="#main-content" className="skip-to-content">
        Skip to main content
      </a>

      <header className="app-header">
        <div className="header-container">
          <div className="logo-group">
            <Link to="/" className="brand-logo" aria-label="MaternAI Home">
              <span className="logo-icon" aria-hidden="true">🤱</span>
              <span className="logo-text">Matern<span className="logo-accent">AI</span></span>
            </Link>
            <span className="tagline">Smart Maternal Health Decision-Support</span>
          </div>

          <nav className="main-nav" aria-label="Main Navigation">
            <Link to="/" className="nav-link">Home</Link>
            
            {isAuthenticated && user && (
              <>
                {user.role === 'MOTHER' && (
                  <Link to="/mother" className="nav-link">Mother Portal</Link>
                )}
                {user.role === 'ASHA' && (
                  <Link to="/asha" className="nav-link">ASHA Portal</Link>
                )}
              </>
            )}
          </nav>

          <div className="auth-status-group">
            {isAuthenticated && user ? (
              <div className="user-profile-badge">
                <span className="user-name">{user.fullName || user.email}</span>
                <span className="user-role-tag">{user.role}</span>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="btn btn-outline btn-sm logout-btn"
                >
                  Sign Out
                </button>
              </div>
            ) : (
              <div className="guest-actions">
                <Link to="/auth/login" className="btn btn-primary btn-sm">
                  Sign In
                </Link>
              </div>
            )}
          </div>
        </div>
      </header>

      <main id="main-content" className="app-main-content">
        <Outlet />
      </main>

      <footer className="app-footer">
        <div className="footer-container">
          <p className="clinical-disclaimer">
            <strong>Clinical Notice:</strong> MaternAI is a decision-support and care-coordination prototype, not an autonomous diagnostic or treatment system. All clinical rules and recommendations require verification with certified healthcare providers.
          </p>
          <p className="copyright-text">
            © {CURRENT_YEAR} MaternAI — Smart Maternal Health Risk Prediction & Care Coordination System
          </p>
        </div>
      </footer>
    </div>
  );
};
