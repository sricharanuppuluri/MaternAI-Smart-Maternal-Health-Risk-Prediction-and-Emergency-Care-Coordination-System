/**
 * Authentication & Profile API service.
 * Interacts with FastAPI /api/v1/auth/profile and related endpoints.
 */

import { apiRequest } from './apiClient';
import type { ProfileCreatePayload, ProfileResponse } from '../types/auth';

export const authService = {
  /**
   * Bootstrap user profile after Supabase signup.
   * Calls POST /api/v1/auth/profile with Bearer token.
   */
  async bootstrapProfile(
    payload: ProfileCreatePayload,
    token?: string | null
  ): Promise<ProfileResponse> {
    return apiRequest<ProfileResponse>('/auth/profile', {
      method: 'POST',
      body: JSON.stringify(payload),
      token,
    });
  },

  /**
   * Fetch current mother's profile.
   * Calls GET /api/v1/mothers/me.
   */
  async getMotherProfile(token?: string | null): Promise<unknown> {
    return apiRequest('/mothers/me', {
      method: 'GET',
      token,
    });
  },
};
