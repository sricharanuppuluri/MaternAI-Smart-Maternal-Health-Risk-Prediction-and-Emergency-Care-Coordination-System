/**
 * Longitudinal Risk Timeline API service.
 * Handles fetching chronological risk assessments and vital trends for a mother.
 * Contract: GET /api/v1/mothers/{id}/risk-timeline
 * 
 * Note: Per Developer 1 frozen contract confirmation, this is the ONLY approved
 * historical read mechanism for Phase 4.
 */

import { apiRequest } from './apiClient';
import type { RiskTimelineResponse } from '../types/mother';

export const timelineService = {
  /**
   * Fetch mother's longitudinal risk assessments and vital history.
   * Calls GET /api/v1/mothers/{id}/risk-timeline with Bearer token.
   */
  async getRiskTimeline(
    motherId: string,
    token?: string | null
  ): Promise<RiskTimelineResponse> {
    return apiRequest<RiskTimelineResponse>(`/mothers/${motherId}/risk-timeline`, {
      method: 'GET',
      token,
    });
  },
};
