/**
 * Standard API response, error, and status types for MaternAI frontend.
 * Conforms to API contract documented in MaternAI End-to-End Documentation Section 22
 * and backend Pydantic schemas in backend/app/schemas/common.py.
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

export interface PaginationParams {
  page?: number;
  size?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  total_pages: number;
}
