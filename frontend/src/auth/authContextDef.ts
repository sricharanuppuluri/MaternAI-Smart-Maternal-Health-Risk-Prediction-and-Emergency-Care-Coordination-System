import { createContext } from 'react';
import type { AuthState, UserRole } from '../types/auth';

export interface AuthContextValue extends AuthState {
  login: (role: UserRole, email?: string) => Promise<void>;
  logout: () => Promise<void>;
  setRole: (role: UserRole) => void;
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined);
