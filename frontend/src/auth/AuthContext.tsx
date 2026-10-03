/**
 * Authentication Provider component for MaternAI.
 *
 * Implements:
 * - Supabase Auth session initialization and onAuthStateChange subscription
 * - Token management (Authorization: Bearer <token>)
 * - Role-based authorization context ('MOTHER' | 'ASHA' | 'ADMIN')
 * - Graceful fallback to client session when Supabase is in local/offline development mode
 */

import React, { useState, useEffect, type ReactNode } from 'react';
import type {
  AuthUser,
  UserRole,
  LoginCredentials,
  RegisterCredentials,
} from '../types/auth';
import { AuthContext, type AuthContextValue } from './authContextDef';
import { supabase, isSupabaseConfigured } from './supabaseClient';

const LOCAL_STORAGE_USER_KEY = 'maternai_user';
const LOCAL_STORAGE_TOKEN_KEY = 'materna_auth_token';

// Generates a structurally valid 3-part JWT for mock/offline local development
function createMockJwt(userId: string, role: UserRole, email: string): string {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const payload = btoa(
    JSON.stringify({
      sub: userId,
      role,
      email,
      iat: Math.floor(Date.now() / 1000),
      exp: Math.floor(Date.now() / 1000) + 3600 * 24,
    })
  );
  const signature = btoa('mock-client-signature');
  return `${header}.${payload}.${signature}`;
}

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
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Synchronize with Supabase Auth session on mount
  useEffect(() => {
    let isMounted = true;

    async function initSession() {
      if (isSupabaseConfigured) {
        try {
          const { data, error: sessionError } = await supabase.auth.getSession();
          if (sessionError) {
            console.warn('Supabase getSession notice:', sessionError.message);
          } else if (data.session && isMounted) {
            const sbUser = data.session.user;
            const userRole: UserRole =
              (sbUser.user_metadata?.role as UserRole) ||
              (sbUser.app_metadata?.role as UserRole) ||
              'MOTHER';

            const authUser: AuthUser = {
              id: sbUser.id,
              email: sbUser.email,
              role: userRole,
              full_name: sbUser.user_metadata?.full_name || sbUser.email || 'User',
              fullName: sbUser.user_metadata?.full_name || sbUser.email || 'User',
              phone: sbUser.phone || sbUser.user_metadata?.phone,
              created_at: sbUser.created_at,
            };

            setUser(authUser);
            setToken(data.session.access_token);
            localStorage.setItem(LOCAL_STORAGE_USER_KEY, JSON.stringify(authUser));
            localStorage.setItem(LOCAL_STORAGE_TOKEN_KEY, data.session.access_token);
          }
        } catch (err: unknown) {
          console.warn('Supabase session initialization notice:', err);
        }
      }

      if (isMounted) {
        setIsLoading(false);
      }
    }

    initSession();

    // Subscribe to Supabase auth state change events
    const { data: authListener } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        if (!isMounted) return;

        if (session) {
          const sbUser = session.user;
          const userRole: UserRole =
            (sbUser.user_metadata?.role as UserRole) ||
            (sbUser.app_metadata?.role as UserRole) ||
            'MOTHER';

          const authUser: AuthUser = {
            id: sbUser.id,
            email: sbUser.email,
            role: userRole,
            full_name: sbUser.user_metadata?.full_name || sbUser.email || 'User',
            fullName: sbUser.user_metadata?.full_name || sbUser.email || 'User',
            phone: sbUser.phone || sbUser.user_metadata?.phone,
            created_at: sbUser.created_at,
          };

          setUser(authUser);
          setToken(session.access_token);
          localStorage.setItem(LOCAL_STORAGE_USER_KEY, JSON.stringify(authUser));
          localStorage.setItem(LOCAL_STORAGE_TOKEN_KEY, session.access_token);
        } else {
          setUser(null);
          setToken(null);
          localStorage.removeItem(LOCAL_STORAGE_USER_KEY);
          localStorage.removeItem(LOCAL_STORAGE_TOKEN_KEY);
        }
        setIsLoading(false);
      }
    );

    return () => {
      isMounted = false;
      authListener?.subscription.unsubscribe();
    };
  }, []);

  const signIn = async (credentials: LoginCredentials): Promise<void> => {
    setIsLoading(true);
    setError(null);

    const selectedRole: UserRole = credentials.role || 'MOTHER';
    const email = credentials.email.trim();

    try {
      if (isSupabaseConfigured && credentials.password) {
        const { data, error: sbError } = await supabase.auth.signInWithPassword({
          email,
          password: credentials.password,
        });

        if (sbError) {
          throw new Error(sbError.message);
        }

        if (data.session) {
          const sbUser = data.session.user;
          const userRole: UserRole =
            (sbUser.user_metadata?.role as UserRole) ||
            (sbUser.app_metadata?.role as UserRole) ||
            selectedRole;

          const authUser: AuthUser = {
            id: sbUser.id,
            email: sbUser.email,
            role: userRole,
            full_name: sbUser.user_metadata?.full_name || email,
            fullName: sbUser.user_metadata?.full_name || email,
            phone: sbUser.phone,
            created_at: sbUser.created_at,
          };

          setUser(authUser);
          setToken(data.session.access_token);
          localStorage.setItem(LOCAL_STORAGE_USER_KEY, JSON.stringify(authUser));
          localStorage.setItem(LOCAL_STORAGE_TOKEN_KEY, data.session.access_token);
          return;
        }
      }

      // Offline / Demo / Mock mode sign in
      const mockId = `mock-${selectedRole.toLowerCase()}-${Date.now()}`;
      const mockToken = createMockJwt(mockId, selectedRole, email);
      const mockUser: AuthUser = {
        id: mockId,
        email: email || `${selectedRole.toLowerCase()}@maternai.org`,
        role: selectedRole,
        full_name:
          selectedRole === 'MOTHER' ? 'Priya Sharma (Mother)' : 'Anita Devi (ASHA Worker)',
        fullName:
          selectedRole === 'MOTHER' ? 'Priya Sharma (Mother)' : 'Anita Devi (ASHA Worker)',
        phone: '+91 9876543210',
        created_at: new Date().toISOString(),
      };

      setUser(mockUser);
      setToken(mockToken);
      localStorage.setItem(LOCAL_STORAGE_USER_KEY, JSON.stringify(mockUser));
      localStorage.setItem(LOCAL_STORAGE_TOKEN_KEY, mockToken);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Authentication failed';
      setError(msg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const signUp = async (credentials: RegisterCredentials): Promise<void> => {
    setIsLoading(true);
    setError(null);

    const email = credentials.email.trim();
    const fullName = credentials.full_name.trim();
    const role: UserRole = credentials.role || 'MOTHER';

    try {
      if (isSupabaseConfigured && credentials.password) {
        const { data, error: sbError } = await supabase.auth.signUp({
          email,
          password: credentials.password,
          options: {
            data: {
              full_name: fullName,
              role,
              phone: credentials.phone || null,
            },
          },
        });

        if (sbError) {
          throw new Error(sbError.message);
        }

        if (data.session) {
          const authUser: AuthUser = {
            id: data.session.user.id,
            email,
            role,
            full_name: fullName,
            fullName,
            phone: credentials.phone || null,
            created_at: data.session.user.created_at,
          };

          setUser(authUser);
          setToken(data.session.access_token);
          localStorage.setItem(LOCAL_STORAGE_USER_KEY, JSON.stringify(authUser));
          localStorage.setItem(LOCAL_STORAGE_TOKEN_KEY, data.session.access_token);
          return;
        }
      }

      // Offline / Demo / Mock mode registration
      const mockId = `mock-${role.toLowerCase()}-${Date.now()}`;
      const mockToken = createMockJwt(mockId, role, email);
      const mockUser: AuthUser = {
        id: mockId,
        email: email || `${role.toLowerCase()}@maternai.org`,
        role,
        full_name: fullName || 'New Registered User',
        fullName: fullName || 'New Registered User',
        phone: credentials.phone || '+91 9876543210',
        created_at: new Date().toISOString(),
      };

      setUser(mockUser);
      setToken(mockToken);
      localStorage.setItem(LOCAL_STORAGE_USER_KEY, JSON.stringify(mockUser));
      localStorage.setItem(LOCAL_STORAGE_TOKEN_KEY, mockToken);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Registration failed';
      setError(msg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const signOut = async (): Promise<void> => {
    setIsLoading(true);
    try {
      if (isSupabaseConfigured) {
        await supabase.auth.signOut();
      }
    } catch (err) {
      console.warn('Supabase signOut notice:', err);
    } finally {
      setUser(null);
      setToken(null);
      setError(null);
      localStorage.removeItem(LOCAL_STORAGE_USER_KEY);
      localStorage.removeItem(LOCAL_STORAGE_TOKEN_KEY);
      setIsLoading(false);
    }
  };

  const setRole = (newRole: UserRole): void => {
    if (user) {
      const updatedUser: AuthUser = { ...user, role: newRole };
      setUser(updatedUser);
      localStorage.setItem(LOCAL_STORAGE_USER_KEY, JSON.stringify(updatedUser));
    }
  };

  const clearError = (): void => {
    setError(null);
  };

  // Backwards compatibility wrappers
  const login = async (role: UserRole, email?: string): Promise<void> => {
    await signIn({ email: email || `${role.toLowerCase()}@maternai.org`, role });
  };

  const logout = async (): Promise<void> => {
    await signOut();
  };

  const value: AuthContextValue = {
    user,
    token,
    role: user?.role || null,
    isAuthenticated: Boolean(user && token),
    isLoading,
    error,
    signIn,
    signUp,
    signOut,
    setRole,
    clearError,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
