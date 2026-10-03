/**
 * MaternAI Frontend API Client
 *
 * Provides a standardized HTTP client layer configured with:
 * - VITE_API_BASE_URL (defaults to /api/v1)
 * - Automatic Authorization: Bearer <token> header when authenticated
 * - Structured error parsing adhering to the MaternAI API error contract
 */

import type { ApiErrorDetail, ApiErrorResponse } from '../types/api';

const DEFAULT_API_BASE_URL = 'http://localhost:8000/api/v1';

export const getApiBaseUrl = (): string => {
  return import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL;
};

export class ApiError extends Error {
  public readonly code: string;
  public readonly status: number;
  public readonly details?: Record<string, unknown>;

  constructor(status: number, errorDetail: ApiErrorDetail) {
    super(errorDetail.message || `API error with status ${status}`);
    this.name = 'ApiError';
    this.code = errorDetail.code || 'UNKNOWN_ERROR';
    this.status = status;
    this.details = errorDetail.details;
  }
}

export interface RequestOptions extends RequestInit {
  token?: string | null;
}

/**
 * Generic fetch wrapper for MaternAI backend API endpoints.
 */
export async function apiRequest<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const baseUrl = getApiBaseUrl().replace(/\/+$/, '');
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const url = `${baseUrl}${cleanEndpoint}`;

  const headers = new Headers(options.headers || {});
  
  if (!headers.has('Content-Type') && options.body && typeof options.body === 'string') {
    headers.set('Content-Type', 'application/json');
  }

  // Inject Bearer token if provided or stored
  const storedToken = typeof localStorage !== 'undefined' ? localStorage.getItem('materna_auth_token') : null;
  const token = options.token ?? storedToken;
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail: ApiErrorDetail = {
      code: `HTTP_${response.status}`,
      message: response.statusText || 'An unexpected server error occurred',
    };

    try {
      const errorJson = (await response.json()) as ApiErrorResponse | { detail?: string };
      if ('error' in errorJson && errorJson.error) {
        errorDetail = errorJson.error;
      } else if ('detail' in errorJson && typeof errorJson.detail === 'string') {
        errorDetail = {
          code: `HTTP_${response.status}`,
          message: errorJson.detail,
        };
      }
    } catch {
      // Fallback to response status text if body is not JSON
    }

    throw new ApiError(response.status, errorDetail);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return {} as T;
  }

  return response.json() as Promise<T>;
}
