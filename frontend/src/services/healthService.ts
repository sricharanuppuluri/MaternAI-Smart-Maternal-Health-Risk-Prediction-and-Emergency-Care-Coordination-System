/**
 * Health check service for MaternAI backend API.
 * Calls /api/v1/health to verify connectivity with the FastAPI backend.
 */

import { apiRequest } from './apiClient';
import type { HealthStatusResponse } from '../types/api';

export const healthService = {
  /**
   * Check backend API v1 health status
   */
  async checkHealth(): Promise<HealthStatusResponse> {
    return apiRequest<HealthStatusResponse>('/health', {
      method: 'GET',
    });
  },
};
