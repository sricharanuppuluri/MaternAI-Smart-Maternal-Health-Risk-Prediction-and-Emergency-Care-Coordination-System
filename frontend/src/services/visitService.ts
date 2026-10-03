/**
 * Visits API service.
 * Handles recording and scheduling ASHA in-person and home visits.
 * Contract: POST /api/v1/visits
 */

import { apiRequest } from './apiClient';
import type { VisitCreate, VisitResponse } from '../types/asha';

export const visitService = {
  /**
   * Schedule or record an ASHA visit.
   * Calls POST /api/v1/visits with Bearer token.
   */
  async createVisit(
    payload: VisitCreate,
    token?: string | null
  ): Promise<VisitResponse> {
    return apiRequest<VisitResponse>('/visits', {
      method: 'POST',
      body: JSON.stringify(payload),
      token,
    });
  },
};
