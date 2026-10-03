/**
 * Alerts & Escalation Workflow API service.
 * Handles querying the alerts queue and updating alert workflow statuses.
 * Contracts:
 * - GET /api/v1/alerts
 * - PATCH /api/v1/alerts/{id}/status
 */

import { apiRequest } from './apiClient';
import type { AlertResponse, AlertStatusUpdate } from '../types/asha';
import type { PaginatedResponse } from '../types/api';

export const alertService = {
  /**
   * List paginated alerts queue.
   * Calls GET /api/v1/alerts with page & size query params and Bearer token.
   */
  async listAlerts(
    page: number = 1,
    size: number = 20,
    token?: string | null
  ): Promise<PaginatedResponse<AlertResponse>> {
    const queryParams = new URLSearchParams({
      page: String(page),
      size: String(size),
    });

    return apiRequest<PaginatedResponse<AlertResponse>>(`/alerts?${queryParams.toString()}`, {
      method: 'GET',
      token,
    });
  },

  /**
   * Update ASHA case workflow status for an alert.
   * Calls PATCH /api/v1/alerts/{id}/status with Bearer token.
   */
  async updateAlertStatus(
    id: string,
    payload: AlertStatusUpdate,
    token?: string | null
  ): Promise<AlertResponse> {
    return apiRequest<AlertResponse>(`/alerts/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
      token,
    });
  },
};
