/**
 * Generic API request hook for handling async state, loading, error, and empty states.
 * Reusable pattern adhering to Phase 4 frontend architecture.
 */

import { useState, useCallback } from 'react';
import type { ApiErrorDetail } from '../types/api';
import { ApiError } from '../services/apiClient';

export interface UseApiState<T> {
  data: T | null;
  isLoading: boolean;
  error: ApiErrorDetail | null;
  isEmpty: boolean;
}

function checkIsEmpty<T>(data: T | null, isLoading: boolean, error: ApiErrorDetail | null): boolean {
  if (isLoading || error !== null || data === null) {
    return false;
  }
  if (Array.isArray(data)) {
    return data.length === 0;
  }
  if (
    typeof data === 'object' &&
    data !== null &&
    'items' in data &&
    Array.isArray((data as { items: unknown[] }).items)
  ) {
    return (data as { items: unknown[] }).items.length === 0;
  }
  return false;
}

export function useApi<T, P extends unknown[]>(
  apiFn: (...args: P) => Promise<T>
) {
  const [state, setState] = useState<Omit<UseApiState<T>, 'isEmpty'>>({
    data: null,
    isLoading: false,
    error: null,
  });

  const execute = useCallback(
    async (...args: P): Promise<T | null> => {
      setState({ data: null, isLoading: true, error: null });
      try {
        const result = await apiFn(...args);
        setState({ data: result, isLoading: false, error: null });
        return result;
      } catch (err: unknown) {
        let errorDetail: ApiErrorDetail;
        if (err instanceof ApiError) {
          errorDetail = {
            code: err.code,
            message: err.message,
            details: err.details,
          };
        } else if (err instanceof Error) {
          errorDetail = {
            code: 'CLIENT_ERROR',
            message: err.message,
          };
        } else {
          errorDetail = {
            code: 'UNKNOWN_ERROR',
            message: 'An unknown error occurred',
          };
        }
        setState({ data: null, isLoading: false, error: errorDetail });
        return null;
      }
    },
    [apiFn]
  );

  const isEmpty = checkIsEmpty(state.data, state.isLoading, state.error);

  return {
    ...state,
    isEmpty,
    execute,
    reset: () => setState({ data: null, isLoading: false, error: null }),
  };
}
