/**
 * Generic API request hook for handling async state, loading, and error states.
 */

import { useState, useCallback } from 'react';
import type { ApiErrorDetail } from '../types/api';
import { ApiError } from '../services/apiClient';

interface UseApiState<T> {
  data: T | null;
  isLoading: boolean;
  error: ApiErrorDetail | null;
}

export function useApi<T, P extends unknown[]>(
  apiFn: (...args: P) => Promise<T>
) {
  const [state, setState] = useState<UseApiState<T>>({
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

  return {
    ...state,
    execute,
    reset: () => setState({ data: null, isLoading: false, error: null }),
  };
}
