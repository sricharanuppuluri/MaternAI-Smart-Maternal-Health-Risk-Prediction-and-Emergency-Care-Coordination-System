/**
 * Authentication and authorization types for MaternAI frontend.
 *
 * Roles correspond to backend Supabase & FastAPI authorization definitions:
 * - MOTHER: Expecting or new mother accessing maternal health tracking and care.
 * - ASHA: Accredited Social Health Activist worker managing assigned cases.
 * - ADMIN: System administrator (future scope, server-controlled).
 */

export type UserRole = 'MOTHER' | 'ASHA' | 'ADMIN';

export interface AuthUser {
  id: string;
  email?: string;
  role: UserRole;
  fullName?: string;
  phone?: string;
  createdAt?: string;
}

export interface AuthState {
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface LoginCredentials {
  email: string;
  password?: string;
  role?: UserRole;
}
