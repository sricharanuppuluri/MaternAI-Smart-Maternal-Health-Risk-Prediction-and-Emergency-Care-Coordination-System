import { createContext } from 'react';
import type { AuthState, UserRole, LoginCredentials, RegisterCredentials } from '../types/auth';

export interface AuthContextValue extends AuthState {
  signIn: (credentials: LoginCredentials) => Promise<void>;
  signUp: (credentials: RegisterCredentials) => Promise<void>;
  signOut: () => Promise<void>;
  setRole: (role: UserRole) => void;
  clearError: () => void;
  // Phase 1 backwards compatibility methods:
  login: (role: UserRole, email?: string) => Promise<void>;
  logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined);
