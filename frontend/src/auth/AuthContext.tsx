/**
 * Authentication Provider component for MaternAI.
 */

import React, { useState, type ReactNode } from 'react';
import type { AuthUser, UserRole } from '../types/auth';
import { AuthContext, type AuthContextValue } from './authContextDef';

const LOCAL_STORAGE_USER_KEY = 'maternai_user';
const LOCAL_STORAGE_TOKEN_KEY = 'materna_auth_token';

function getInitialUser(): AuthUser | null {
  try {
    const stored = localStorage.getItem(LOCAL_STORAGE_USER_KEY);
    return stored ? JSON.parse(stored) : null;
  } catch {
    return null;
  }
}

function getInitialToken(): string | null {
  try {
    return localStorage.getItem(LOCAL_STORAGE_TOKEN_KEY);
  } catch {
    return null;
  }
}

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(getInitialUser);
  const [token, setToken] = useState<string | null>(getInitialToken);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const login = async (role: UserRole, email?: string): Promise<void> => {
    setIsLoading(true);
    try {
      const mockUser: AuthUser = {
        id: `mock-${role.toLowerCase()}-${Date.now()}`,
        email: email || `${role.toLowerCase()}@maternai.org`,
        role,
        fullName: role === 'MOTHER' ? 'Priya Sharma (Mother)' : 'Anita Devi (ASHA Worker)',
        phone: '+91 9876543210',
        createdAt: new Date().toISOString(),
      };
      const mockToken = `mock-jwt-token-${role.toLowerCase()}`;

      setUser(mockUser);
      setToken(mockToken);
      localStorage.setItem(LOCAL_STORAGE_USER_KEY, JSON.stringify(mockUser));
      localStorage.setItem(LOCAL_STORAGE_TOKEN_KEY, mockToken);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async (): Promise<void> => {
    setUser(null);
    setToken(null);
    localStorage.removeItem(LOCAL_STORAGE_USER_KEY);
    localStorage.removeItem(LOCAL_STORAGE_TOKEN_KEY);
  };

  const setRole = (role: UserRole): void => {
    if (user) {
      const updatedUser = { ...user, role };
      setUser(updatedUser);
      localStorage.setItem(LOCAL_STORAGE_USER_KEY, JSON.stringify(updatedUser));
    }
  };

  const value: AuthContextValue = {
    user,
    token,
    isAuthenticated: Boolean(user),
    isLoading,
    login,
    logout,
    setRole,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
