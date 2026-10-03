/**
 * ProtectedRoute guard component.
 *
 * Ensures:
 * 1. User is authenticated before accessing protected portals.
 * 2. Role-based isolation: Mother cannot access ASHA routes, and ASHA cannot access Mother routes.
 */

import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from './useAuth';
import type { UserRole } from '../types/auth';

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: UserRole[];
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  allowedRoles,
}) => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', fontFamily: 'system-ui, sans-serif' }}>
        <p>Loading MaternAI session...</p>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    // Redirect to login while preserving target route for post-login navigation
    return <Navigate to="/auth/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    // Role mismatch: redirect to appropriate portal
    const fallbackPath = user.role === 'ASHA' ? '/asha' : '/mother';
    return <Navigate to={fallbackPath} replace />;
  }

  return <>{children}</>;
};
