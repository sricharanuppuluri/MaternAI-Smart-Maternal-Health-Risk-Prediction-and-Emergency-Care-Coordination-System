/**
 * Standard API response, error, and status types for MaternAI frontend.
 * Conforms to API contract documented in MaternAI End-to-End Documentation Section 22.
 */

export interface ApiErrorDetail {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface ApiErrorResponse {
  error: ApiErrorDetail;
}

export interface HealthStatusResponse {
  status: string;
  app: string;
  version: string;
  environment: string;
}

export interface ApiResponse<T> {
  data?: T;
  error?: ApiErrorDetail;
  status: number;
}
