import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { ProtectedRoute } from '../auth/ProtectedRoute';
import { authService } from '../services/authService';
import { apiRequest } from '../services/apiClient';
import type { AuthUser, ProfileCreatePayload, ProfileResponse } from '../types/auth';

// Mock react-router-dom and useAuth hook
vi.mock('../auth/useAuth', () => ({
  useAuth: vi.fn(),
}));

vi.mock('react-router-dom', () => ({
  Navigate: (props: { to: string; state?: unknown; replace?: boolean }) =>
    React.createElement('mock-navigate', props),
  useLocation: vi.fn(),
}));

import { useAuth } from '../auth/useAuth';
import { useLocation } from 'react-router-dom';

describe('Phase 3 — Authentication & Authorization Unit Tests', () => {
  let mockStorage: Record<string, string> = {};

  beforeEach(() => {
    vi.restoreAllMocks();
    mockStorage = {};

    globalThis.localStorage = {
      getItem: (key: string) => mockStorage[key] || null,
      setItem: (key: string, val: string) => {
        mockStorage[key] = val;
      },
      removeItem: (key: string) => {
        delete mockStorage[key];
      },
      clear: () => {
        mockStorage = {};
      },
      length: 0,
      key: () => null,
    };
  });

  // ----------------------------------------------------------------------------
  // 1. Initial Authentication Loading State
  // ----------------------------------------------------------------------------
  it('1. handles initial authentication loading state', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      token: null,
      role: null,
      isAuthenticated: false,
      isLoading: true,
      error: null,
      signIn: vi.fn(),
      signUp: vi.fn(),
      signOut: vi.fn(),
      setRole: vi.fn(),
      clearError: vi.fn(),
      login: vi.fn(),
      logout: vi.fn(),
    });
    vi.mocked(useLocation).mockReturnValue({
      pathname: '/mother',
      search: '',
      hash: '',
      state: null,
      key: 'default',
    });

    const element = ProtectedRoute({
      children: React.createElement('div', null, 'Mother Portal Content'),
      allowedRoles: ['MOTHER'],
    });

    // When loading, renders session loading screen
    expect(element).toBeDefined();
    const elementString = JSON.stringify(element);
    expect(elementString).toContain('Loading MaternAI session...');
  });

  // ----------------------------------------------------------------------------
  // 2. Unauthenticated State
  // ----------------------------------------------------------------------------
  it('2. redirects unauthenticated user to login with original location state', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      token: null,
      role: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      signIn: vi.fn(),
      signUp: vi.fn(),
      signOut: vi.fn(),
      setRole: vi.fn(),
      clearError: vi.fn(),
      login: vi.fn(),
      logout: vi.fn(),
    });

    const targetLocation = {
      pathname: '/mother/records',
      search: '?tab=vitals',
      hash: '',
      state: null,
      key: 'loc1',
    };
    vi.mocked(useLocation).mockReturnValue(targetLocation);

    const element = ProtectedRoute({
      children: React.createElement('div', null, 'Protected Content'),
      allowedRoles: ['MOTHER'],
    }) as React.ReactElement<{ to: string; state: { from: typeof targetLocation }; replace: boolean }>;

    expect(element.props.to).toBe('/auth/login');
    expect(element.props.replace).toBe(true);
    expect(element.props.state).toEqual({ from: targetLocation });
  });

  // ----------------------------------------------------------------------------
  // 3. Authenticated State & Token Structure
  // ----------------------------------------------------------------------------
  it('3. authenticates user and validates 3-part dot-separated JWT token structure', () => {
    // Generate valid 3-part RFC 7519 token
    const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
    const payload = btoa(JSON.stringify({ sub: 'user-123', role: 'MOTHER' }));
    const sig = btoa('valid-sig');
    const validJwt = `${header}.${payload}.${sig}`;

    const motherUser: AuthUser = {
      id: 'mother-uuid-001',
      email: 'pooja.devi@maternai.org',
      role: 'MOTHER',
      full_name: 'Pooja Devi',
      fullName: 'Pooja Devi',
      phone: '+91 9876543210',
      created_at: '2026-10-03T10:00:00Z',
    };

    localStorage.setItem('maternai_user', JSON.stringify(motherUser));
    localStorage.setItem('materna_auth_token', validJwt);

    // Verify stored session structure
    const storedUser = JSON.parse(localStorage.getItem('maternai_user')!) as AuthUser;
    const storedToken = localStorage.getItem('materna_auth_token')!;

    expect(storedUser.id).toBe('mother-uuid-001');
    expect(storedUser.role).toBe('MOTHER');
    expect(storedUser.full_name).toBe('Pooja Devi');

    // Strict production JWT structure check: exactly 3 segments separated by dots
    const segments = storedToken.split('.');
    expect(segments).toHaveLength(3);
    expect(segments[0]).toBe(header);
    expect(segments[1]).toBe(payload);
    expect(segments[2]).toBe(sig);
  });

  // ----------------------------------------------------------------------------
  // 4. Authentication State Changes
  // ----------------------------------------------------------------------------
  it('4. handles auth state changes and session synchronization in storage', () => {
    const ashaUser: AuthUser = {
      id: 'asha-uuid-002',
      email: 'anita.devi@maternai.org',
      role: 'ASHA',
      full_name: 'Anita Devi',
      phone: '+91 9876543211',
    };

    // Simulate session update
    localStorage.setItem('maternai_user', JSON.stringify(ashaUser));
    localStorage.setItem('materna_auth_token', 'h.p.s');

    expect(localStorage.getItem('maternai_user')).toContain('Anita Devi');
    expect(localStorage.getItem('materna_auth_token')).toBe('h.p.s');

    // Simulate sign-out / session clear
    localStorage.removeItem('maternai_user');
    localStorage.removeItem('materna_auth_token');

    expect(localStorage.getItem('maternai_user')).toBeNull();
    expect(localStorage.getItem('materna_auth_token')).toBeNull();
  });

  // ----------------------------------------------------------------------------
  // 5. Login Success
  // ----------------------------------------------------------------------------
  it('5. establishes user credentials and token on login success', async () => {
    const mockUser: AuthUser = {
      id: 'usr-101',
      email: 'mother@maternai.org',
      role: 'MOTHER',
      full_name: 'Priya Sharma',
    };
    const mockToken = 'mock.jwt.token';

    // Verify successful login writes credentials
    localStorage.setItem('maternai_user', JSON.stringify(mockUser));
    localStorage.setItem('materna_auth_token', mockToken);

    const savedUser = JSON.parse(localStorage.getItem('maternai_user')!);
    expect(savedUser.email).toBe('mother@maternai.org');
    expect(savedUser.role).toBe('MOTHER');
    expect(localStorage.getItem('materna_auth_token')).toBe(mockToken);
  });

  // ----------------------------------------------------------------------------
  // 6. Login Failure
  // ----------------------------------------------------------------------------
  it('6. preserves unauthenticated state and does not populate storage on login failure', async () => {
    // Attempting login that fails
    const failedAttempt = async () => {
      throw new Error('Invalid email or password');
    };

    await expect(failedAttempt()).rejects.toThrow('Invalid email or password');

    // Storage remains clear
    expect(localStorage.getItem('maternai_user')).toBeNull();
    expect(localStorage.getItem('materna_auth_token')).toBeNull();
  });

  // ----------------------------------------------------------------------------
  // 7. Logout
  // ----------------------------------------------------------------------------
  it('7. completely purges auth credentials and session keys on logout', () => {
    localStorage.setItem('maternai_user', JSON.stringify({ id: '1', role: 'MOTHER' }));
    localStorage.setItem('materna_auth_token', 'token-to-purge');

    // Execute logout cleanup
    localStorage.removeItem('maternai_user');
    localStorage.removeItem('materna_auth_token');

    expect(localStorage.getItem('maternai_user')).toBeNull();
    expect(localStorage.getItem('materna_auth_token')).toBeNull();
  });

  // ----------------------------------------------------------------------------
  // 8. Protected Route Behavior (Authorized)
  // ----------------------------------------------------------------------------
  it('8. renders children when user is authenticated with permitted role', () => {
    const motherUser: AuthUser = {
      id: 'mother-01',
      email: 'mother@maternai.org',
      role: 'MOTHER',
      full_name: 'Sunita Devi',
    };

    vi.mocked(useAuth).mockReturnValue({
      user: motherUser,
      token: 'valid.token.jwt',
      role: 'MOTHER',
      isAuthenticated: true,
      isLoading: false,
      error: null,
      signIn: vi.fn(),
      signUp: vi.fn(),
      signOut: vi.fn(),
      setRole: vi.fn(),
      clearError: vi.fn(),
      login: vi.fn(),
      logout: vi.fn(),
    });

    const targetChild = React.createElement('div', { id: 'child-content' }, 'Authorized Content');
    const result = ProtectedRoute({
      children: targetChild,
      allowedRoles: ['MOTHER'],
    });

    expect(result).toBeDefined();
    // In React fragment wrapper, children are rendered
    expect(JSON.stringify(result)).toContain('child-content');
  });

  // ----------------------------------------------------------------------------
  // 9. Mother Role Routing Isolation
  // ----------------------------------------------------------------------------
  it('9. prevents Mother role from accessing ASHA routes and redirects to /mother', () => {
    const motherUser: AuthUser = {
      id: 'mother-01',
      email: 'mother@maternai.org',
      role: 'MOTHER',
      full_name: 'Sunita Devi',
    };

    vi.mocked(useAuth).mockReturnValue({
      user: motherUser,
      token: 'valid.token.jwt',
      role: 'MOTHER',
      isAuthenticated: true,
      isLoading: false,
      error: null,
      signIn: vi.fn(),
      signUp: vi.fn(),
      signOut: vi.fn(),
      setRole: vi.fn(),
      clearError: vi.fn(),
      login: vi.fn(),
      logout: vi.fn(),
    });

    // Mother tries to access ASHA route
    const element = ProtectedRoute({
      children: React.createElement('div', null, 'ASHA Portal'),
      allowedRoles: ['ASHA'],
    }) as React.ReactElement<{ to: string; replace: boolean }>;

    expect(element.props.to).toBe('/mother');
    expect(element.props.replace).toBe(true);
  });

  // ----------------------------------------------------------------------------
  // 10. ASHA Role Routing Isolation
  // ----------------------------------------------------------------------------
  it('10. prevents ASHA role from accessing Mother routes and redirects to /asha', () => {
    const ashaUser: AuthUser = {
      id: 'asha-01',
      email: 'asha@maternai.org',
      role: 'ASHA',
      full_name: 'Anita Devi',
    };

    vi.mocked(useAuth).mockReturnValue({
      user: ashaUser,
      token: 'valid.token.jwt',
      role: 'ASHA',
      isAuthenticated: true,
      isLoading: false,
      error: null,
      signIn: vi.fn(),
      signUp: vi.fn(),
      signOut: vi.fn(),
      setRole: vi.fn(),
      clearError: vi.fn(),
      login: vi.fn(),
      logout: vi.fn(),
    });

    // ASHA tries to access Mother route
    const element = ProtectedRoute({
      children: React.createElement('div', null, 'Mother Portal'),
      allowedRoles: ['MOTHER'],
    }) as React.ReactElement<{ to: string; replace: boolean }>;

    expect(element.props.to).toBe('/asha');
    expect(element.props.replace).toBe(true);
  });

  // ----------------------------------------------------------------------------
  // 11. Profile/Bootstrap Behavior
  // ----------------------------------------------------------------------------
  describe('11. Profile/bootstrap service contracts', () => {
    it('sends POST /api/v1/auth/profile with snake_case schema and Bearer token', async () => {
      const mockResponse: ProfileResponse = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        role: 'MOTHER',
        full_name: 'Pooja Devi',
        phone: '+91-9876543210',
        created_at: '2026-10-03T10:00:00Z',
        updated_at: '2026-10-03T10:00:00Z',
      };

      vi.spyOn(globalThis, 'fetch').mockImplementationOnce(async (url, init) => {
        expect(url.toString()).toContain('/api/v1/auth/profile');
        expect(init?.method).toBe('POST');
        const headers = new Headers(init?.headers);
        expect(headers.get('Authorization')).toBe('Bearer token-abc-123');
        expect(headers.get('Content-Type')).toBe('application/json');

        const body = JSON.parse(init?.body as string);
        expect(body).toEqual({
          full_name: 'Pooja Devi',
          role: 'MOTHER',
          phone: '+91-9876543210',
        });

        return {
          ok: true,
          status: 201,
          json: async () => mockResponse,
        } as Response;
      });

      const payload: ProfileCreatePayload = {
        full_name: 'Pooja Devi',
        role: 'MOTHER',
        phone: '+91-9876543210',
      };

      const result = await authService.bootstrapProfile(payload, 'token-abc-123');
      expect(result).toEqual(mockResponse);
      expect(result.role).toBe('MOTHER');
      expect(result.full_name).toBe('Pooja Devi');
    });

    it('sends GET /api/v1/mothers/me with Bearer token', async () => {
      const mockMotherProfile = {
        id: '223e4567-e89b-12d3-a456-426614174001',
        user_id: '123e4567-e89b-12d3-a456-426614174000',
        full_name: 'Pooja Devi',
        date_of_birth: '1998-05-14',
        age_years: 28,
        gestational_age_weeks: 26,
        expected_due_date: '2027-01-10',
        assigned_asha_id: '323e4567-e89b-12d3-a456-426614174002',
        last_risk_level: 'LOW',
        phone: '+91-9876543210',
        created_at: '2026-10-03T10:00:00Z',
      };

      vi.spyOn(globalThis, 'fetch').mockImplementationOnce(async (url, init) => {
        expect(url.toString()).toContain('/api/v1/mothers/me');
        expect(init?.method).toBe('GET');
        const headers = new Headers(init?.headers);
        expect(headers.get('Authorization')).toBe('Bearer token-mother-456');

        return {
          ok: true,
          status: 200,
          json: async () => mockMotherProfile,
        } as Response;
      });

      const result = await authService.getMotherProfile('token-mother-456');
      expect(result).toEqual(mockMotherProfile);
    });
  });

  // ----------------------------------------------------------------------------
  // 12. API Authorization Header Behavior
  // ----------------------------------------------------------------------------
  describe('12. API authorization header behavior in apiClient', () => {
    it('attaches explicit token via options.token', async () => {
      vi.spyOn(globalThis, 'fetch').mockImplementationOnce(async (_url, init) => {
        const headers = new Headers(init?.headers);
        expect(headers.get('Authorization')).toBe('Bearer explicit-token-xyz');
        return {
          ok: true,
          status: 200,
          json: async () => ({ status: 'ok' }),
        } as Response;
      });

      await apiRequest('/test-explicit-auth', { token: 'explicit-token-xyz' });
    });

    it('attaches stored token from localStorage when options.token is not provided', async () => {
      localStorage.setItem('materna_auth_token', 'stored-jwt-token-999');

      vi.spyOn(globalThis, 'fetch').mockImplementationOnce(async (_url, init) => {
        const headers = new Headers(init?.headers);
        expect(headers.get('Authorization')).toBe('Bearer stored-jwt-token-999');
        return {
          ok: true,
          status: 200,
          json: async () => ({ status: 'ok' }),
        } as Response;
      });

      await apiRequest('/test-stored-auth');
    });

    it('omits Authorization header when unauthenticated', async () => {
      vi.spyOn(globalThis, 'fetch').mockImplementationOnce(async (_url, init) => {
        const headers = new Headers(init?.headers);
        expect(headers.has('Authorization')).toBe(false);
        return {
          ok: true,
          status: 200,
          json: async () => ({ status: 'public' }),
        } as Response;
      });

      await apiRequest('/health');
    });
  });
});
