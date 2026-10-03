import { describe, it, expect, vi, beforeEach } from 'vitest';
import { getApiBaseUrl, apiRequest } from '../services/apiClient';

describe('apiClient', () => {
  let mockStorage: Record<string, string> = {};

  beforeEach(() => {
    vi.restoreAllMocks();
    mockStorage = {};

    globalThis.localStorage = {
      getItem: (key: string) => mockStorage[key] || null,
      setItem: (key: string, val: string) => { mockStorage[key] = val; },
      removeItem: (key: string) => { delete mockStorage[key]; },
      clear: () => { mockStorage = {}; },
      length: 0,
      key: () => null,
    };
  });

  it('reads VITE_API_BASE_URL or provides sensible default', () => {
    const url = getApiBaseUrl();
    expect(url).toBeDefined();
    expect(typeof url).toBe('string');
  });

  it('correctly constructs URLs and executes fetch with JSON response', async () => {
    const mockData = { status: 'healthy', app: 'MaternAI', version: '0.1.0', environment: 'test' };
    
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockData,
    } as Response);

    const result = await apiRequest<{ status: string }>('/health');
    expect(result).toEqual(mockData);
    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
  });

  it('attaches Bearer token from localStorage when available', async () => {
    localStorage.setItem('materna_auth_token', 'test-token-123');

    vi.spyOn(globalThis, 'fetch').mockImplementationOnce(async (_url, init) => {
      const headers = new Headers(init?.headers);
      expect(headers.get('Authorization')).toBe('Bearer test-token-123');
      return {
        ok: true,
        status: 200,
        json: async () => ({ success: true }),
      } as Response;
    });

    await apiRequest('/test-auth');
  });

  it('throws ApiError with code and details on HTTP error response', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: false,
      status: 400,
      statusText: 'Bad Request',
      json: async () => ({
        error: {
          code: 'VALIDATION_ERROR',
          message: 'Invalid blood pressure range',
          details: { field: 'systolic_bp' },
        },
      }),
    } as Response);

    await expect(apiRequest('/health-records')).rejects.toThrow('Invalid blood pressure range');
  });
});
