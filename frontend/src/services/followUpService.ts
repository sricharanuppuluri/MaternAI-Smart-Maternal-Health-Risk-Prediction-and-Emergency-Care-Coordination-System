/**
 * Follow-up Task API service.
 * Handles scheduling ASHA follow-up tasks for assigned mothers.
 * Contract: POST /api/v1/followups
 */

import { apiRequest } from './apiClient';
import type { FollowUpCreate, FollowUpResponse } from '../types/asha';

export const followUpService = {
  /**
   * Schedule an ASHA follow-up task.
   * Calls POST /api/v1/followups with Bearer token.
   */
  async createFollowUp(
    payload: FollowUpCreate,
    token?: string | null
  ): Promise<FollowUpResponse> {
    return apiRequest<FollowUpResponse>('/followups', {
      method: 'POST',
      body: JSON.stringify(payload),
      token,
    });
  },
};
