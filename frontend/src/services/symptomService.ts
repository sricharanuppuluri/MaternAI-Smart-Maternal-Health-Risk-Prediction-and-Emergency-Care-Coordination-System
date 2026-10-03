/**
 * Symptom Logging API service.
 * Handles recording maternal symptom reports.
 * Contract: POST /api/v1/symptoms
 * 
 * Note: Direct GET /symptoms is intentionally not implemented per frozen contracts.
 */

import { apiRequest } from './apiClient';
import type { SymptomSubmission, SymptomResponse } from '../types/mother';

export const symptomService = {
  /**
   * Submit structured maternal symptoms.
   * Calls POST /api/v1/symptoms with Bearer token.
   */
  async recordSymptoms(
    payload: SymptomSubmission,
    token?: string | null
  ): Promise<SymptomResponse[]> {
    return apiRequest<SymptomResponse[]>('/symptoms', {
      method: 'POST',
      body: JSON.stringify(payload),
      token,
    });
  },
};
