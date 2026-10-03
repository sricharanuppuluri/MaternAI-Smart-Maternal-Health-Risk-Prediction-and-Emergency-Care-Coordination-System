/**
 * Authentication and authorization types for MaternAI frontend.
 *
 * Roles correspond to backend Supabase & FastAPI authorization definitions:
 * - MOTHER: Expecting or new mother accessing maternal health tracking and care.
 * - ASHA: Accredited Social Health Activist worker managing assigned cases.
 * - ADMIN: System administrator (server-controlled; client cannot self-assign).
 */

export type UserRole = 'MOTHER' | 'ASHA' | 'ADMIN';

export interface ProfileCreatePayload {
  full_name: string;
  role: UserRole;
  phone?: string | null;
}

export interface ProfileResponse {
  id: string;
  role: UserRole;
  full_name: string;
  phone?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AuthUser {
  id: string;
  email?: string;
  role: UserRole;
  full_name: string;
  fullName?: string; // Phase 1 compatibility alias
  phone?: string | null;
  created_at?: string;
}

export interface AuthState {
  user: AuthUser | null;
  token: string | null;
  role: UserRole | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface LoginCredentials {
  email: string;
  password?: string;
  role?: UserRole;
}

export interface RegisterCredentials {
  email: string;
  password?: string;
  full_name: string;
  role: UserRole;
  phone?: string;
}
