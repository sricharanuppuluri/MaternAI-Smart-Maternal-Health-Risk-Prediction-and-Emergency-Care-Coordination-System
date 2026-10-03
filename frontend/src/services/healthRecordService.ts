/**
 * Health Record API service.
 * Handles recording maternal vital signs and measurements.
 * Contract: POST /api/v1/health-records
 * 
 * Note: Historical records are queried exclusively via GET /mothers/{id}/risk-timeline.
 * Direct GET /health-records is intentionally not implemented per frozen contracts.
 */

import { apiRequest } from './apiClient';
import type { HealthRecordCreate, HealthRecordResponse } from '../types/mother';

export const healthRecordService = {
  /**
   * Record maternal vital signs and measurements.
   * Calls POST /api/v1/health-records with Bearer token.
   */
  async createHealthRecord(
    payload: HealthRecordCreate,
    token?: string | null
  ): Promise<HealthRecordResponse> {
    return apiRequest<HealthRecordResponse>('/health-records', {
      method: 'POST',
      body: JSON.stringify(payload),
      token,
    });
  },
};
