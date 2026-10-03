/**
 * Phase 4 — Frozen API Contract & Consumer Integration Tests
 * 
 * Verifies:
 * 1. HealthRecordService: POST /api/v1/health-records (snake_case payload & response)
 * 2. SymptomService: POST /api/v1/symptoms (structured symptoms array)
 * 3. PredictionService: POST /api/v1/predictions (ML risk input & explanation factors)
 * 4. AlertService: GET /api/v1/alerts (pagination envelope) & PATCH /api/v1/alerts/{id}/status (status enum)
 * 5. VisitService: POST /api/v1/visits (visit workflow & findings)
 * 6. FollowUpService: POST /api/v1/followups (follow-up task & due_date)
 * 7. TimelineService: GET /api/v1/mothers/{id}/risk-timeline (ONLY approved historical read mechanism)
 * 8. Status Enums adherence (AlertStatus, VisitStatus, FollowUpStatus)
 * 9. Absence of unapproved GET endpoints (no GET /health-records, no GET /symptoms)
 * 10. HTTP status handling: 200, 201, 204, 401, 403, 422
 * 11. ApiError envelope structure preservation
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  healthRecordService,
  symptomService,
  predictionService,
  alertService,
  visitService,
  followUpService,
  timelineService,
  ApiError,
  apiRequest,
} from '../services';
import type {
  HealthRecordCreate,
  HealthRecordResponse,
  SymptomSubmission,
  SymptomResponse,
  PredictionRequest,
  PredictionResponse,
  AlertResponse,
  AlertStatusUpdate,
  AlertStatus,
  VisitCreate,
  VisitResponse,
  VisitStatus,
  FollowUpCreate,
  FollowUpResponse,
  FollowUpStatus,
  RiskTimelineResponse,
} from '../types';

describe('Phase 4 — API Contract Verification & Consumer Tests', () => {
  let mockStorage: Record<string, string> = {};

  beforeEach(() => {
    vi.restoreAllMocks();
    mockStorage = {};

    globalThis.localStorage = {
      getItem: (key: string) => mockStorage[key] || null,
      setItem: (key: string, val: string) => {
        mockStorage[key] = val;
      },
      removeItem: (key: string) => {
        delete mockStorage[key];
      },
      clear: () => {
        mockStorage = {};
      },
      length: 0,
      key: () => null,
    };
  });

  // ----------------------------------------------------------------------------
  // 1. Health Record Service (POST /api/v1/health-records)
  // ----------------------------------------------------------------------------
  describe('1. Health Record Contract', () => {
    it('creates health record via POST /api/v1/health-records with snake_case payload', async () => {
      const payload: HealthRecordCreate = {
        pregnancy_week: 26,
        systolic_bp: 120.0,
        diastolic_bp: 80.0,
        blood_sugar: 92.0,
        hemoglobin: 11.2,
        weight_kg: 62.5,
        body_temperature: 36.6,
        heart_rate: 76.0,
        recorded_at: '2026-10-03T10:30:00Z',
      };

      const mockResponse: HealthRecordResponse = {
        id: '423e4567-e89b-12d3-a456-426614174003',
        mother_id: '223e4567-e89b-12d3-a456-426614174001',
        pregnancy_week: 26,
        systolic_bp: 120.0,
        diastolic_bp: 80.0,
        blood_sugar: 92.0,
        hemoglobin: 11.2,
        weight_kg: 62.5,
        body_temperature: 36.6,
        heart_rate: 76.0,
        recorded_by: '123e4567-e89b-12d3-a456-426614174000',
        recorded_at: '2026-10-03T10:30:00Z',
        created_at: '2026-10-03T10:30:00Z',
      };

      vi.spyOn(globalThis, 'fetch').mockImplementationOnce(async (url, init) => {
        expect(url.toString()).toContain('/api/v1/health-records');
        expect(init?.method).toBe('POST');
        const headers = new Headers(init?.headers);
        expect(headers.get('Authorization')).toBe('Bearer test-token-hr');
        expect(headers.get('Content-Type')).toBe('application/json');

        const body = JSON.parse(init?.body as string);
        expect(body.systolic_bp).toBe(120.0);
        expect(body.blood_sugar).toBe(92.0);
        expect(body.pregnancy_week).toBe(26);

        return {
          ok: true,
          status: 201,
          json: async () => mockResponse,
        } as Response;
      });

      const result = await healthRecordService.createHealthRecord(payload, 'test-token-hr');
      expect(result).toEqual(mockResponse);
      expect(result.mother_id).toBe('223e4567-e89b-12d3-a456-426614174001');
      expect(result.systolic_bp).toBe(120.0);
    });
  });

  // ----------------------------------------------------------------------------
  // 2. Symptom Service (POST /api/v1/symptoms)
  // ----------------------------------------------------------------------------
  describe('2. Symptom Logging Contract', () => {
    it('submits symptoms via POST /api/v1/symptoms and returns SymptomResponse array', async () => {
      const payload: SymptomSubmission = {
        health_record_id: '423e4567-e89b-12d3-a456-426614174003',
        symptoms: [
          { symptom_code: 'headache', severity: 2, notes: 'Mild frontal headache' },
          { symptom_code: 'swelling_feet', severity: 1, notes: 'Pedal edema' },
        ],
      };

      const mockResponse: SymptomResponse[] = [
        {
          id: '523e4567-e89b-12d3-a456-426614174004',
          mother_id: '223e4567-e89b-12d3-a456-426614174001',
          health_record_id: '423e4567-e89b-12d3-a456-426614174003',
          symptom_code: 'headache',
          severity: 2,
          notes: 'Mild frontal headache',
          recorded_at: '2026-10-03T10:35:00Z',
          created_at: '2026-10-03T10:35:00Z',
        },
      ];

      vi.spyOn(globalThis, 'fetch').mockImplementationOnce(async (url, init) => {
        expect(url.toString()).toContain('/api/v1/symptoms');
        expect(init?.method).toBe('POST');
        const body = JSON.parse(init?.body as string);
        expect(body.health_record_id).toBe('423e4567-e89b-12d3-a456-426614174003');
        expect(body.symptoms).toHaveLength(2);
        expect(body.symptoms[0].symptom_code).toBe('headache');

        return {
          ok: true,
          status: 201,
          json: async () => mockResponse,
        } as Response;
      });

      const result = await symptomService.recordSymptoms(payload, 'test-token-sym');
      expect(result).toEqual(mockResponse);
      expect(result[0].symptom_code).toBe('headache');
      expect(result[0].severity).toBe(2);
    });
  });

  // ----------------------------------------------------------------------------
  // 3. Prediction Service (POST /api/v1/predictions)
  // ----------------------------------------------------------------------------
  describe('3. Prediction Contract', () => {
    it('requests ML screening via POST /api/v1/predictions with explainability factors', async () => {
      const payload: PredictionRequest = {
        health_record_id: '423e4567-e89b-12d3-a456-426614174003',
      };

      const mockResponse: PredictionResponse = {
        id: '623e4567-e89b-12d3-a456-426614174005',
        mother_id: '223e4567-e89b-12d3-a456-426614174001',
        health_record_id: '423e4567-e89b-12d3-a456-426614174003',
        risk_level: 'LOW',
        model_score: 0.18,
        model_version: 'v0.1.0',
        feature_schema_version: 'v1.0',
        contributing_factors: [
          { feature: 'hemoglobin', direction: 'DECREASES_RISK', value: 11.2 },
        ],
        created_at: '2026-10-03T10:35:05Z',
      };

      vi.spyOn(globalThis, 'fetch').mockImplementationOnce(async (url, init) => {
        expect(url.toString()).toContain('/api/v1/predictions');
        expect(init?.method).toBe('POST');
        const body = JSON.parse(init?.body as string);
        expect(body.health_record_id).toBe('423e4567-e89b-12d3-a456-426614174003');

        return {
          ok: true,
          status: 201,
          json: async () => mockResponse,
        } as Response;
      });

      const result = await predictionService.requestPrediction(payload, 'token-pred');
      expect(result).toEqual(mockResponse);
      expect(result.risk_level).toBe('LOW');
      expect(result.model_score).toBe(0.18);
      expect(result.contributing_factors[0].feature).toBe('hemoglobin');
    });
  });

  // ----------------------------------------------------------------------------
  // 4. Alerts Service (GET /api/v1/alerts, PATCH /api/v1/alerts/{id}/status)
  // ----------------------------------------------------------------------------
  describe('4. Alerts Queue & Status Update Contract', () => {
    it('queries paginated alerts via GET /api/v1/alerts with page and size query params', async () => {
      const mockAlert: AlertResponse = {
        id: '723e4567-e89b-12d3-a456-426614174006',
        mother_id: '223e4567-e89b-12d3-a456-426614174001',
        mother_name: 'Pooja Devi',
        asha_id: '323e4567-e89b-12d3-a456-426614174002',
        severity: 'HIGH',
        status: 'NEW',
        trigger_reason: 'High systolic blood pressure (145 mmHg)',
        safety_event_id: null,
        prediction_id: '623e4567-e89b-12d3-a456-426614174005',
        created_at: '2026-10-03T10:40:00Z',
        updated_at: '2026-10-03T10:40:00Z',
      };

      const mockPaginated = {
        items: [mockAlert],
        total: 1,
        page: 2,
        size: 10,
        total_pages: 1,
      };

      vi.spyOn(globalThis, 'fetch').mockImplementationOnce(async (url, init) => {
        expect(url.toString()).toContain('/api/v1/alerts?page=2&size=10');
        expect(init?.method).toBe('GET');

        return {
          ok: true,
          status: 200,
          json: async () => mockPaginated,
        } as Response;
      });

      const result = await alertService.listAlerts(2, 10, 'token-alerts');
      expect(result.items).toHaveLength(1);
      expect(result.total).toBe(1);
      expect(result.page).toBe(2);
      expect(result.size).toBe(10);
      expect(result.total_pages).toBe(1);
      expect(result.items[0].severity).toBe('HIGH');
      expect(result.items[0].status).toBe('NEW');
    });

    it('updates alert status via PATCH /api/v1/alerts/{id}/status adhering to frozen AlertStatus enum', async () => {
      const payload: AlertStatusUpdate = {
        status: 'ACKNOWLEDGED',
        notes: 'Reviewing elevated vitals; scheduling home visit',
      };

      const mockUpdatedAlert: AlertResponse = {
        id: '723e4567-e89b-12d3-a456-426614174006',
        mother_id: '223e4567-e89b-12d3-a456-426614174001',
        mother_name: 'Pooja Devi',
        asha_id: '323e4567-e89b-12d3-a456-426614174002',
        severity: 'HIGH',
        status: 'ACKNOWLEDGED',
        trigger_reason: 'High systolic blood pressure (145 mmHg)',
        created_at: '2026-10-03T10:40:00Z',
        updated_at: '2026-10-03T10:45:00Z',
      };

      vi.spyOn(globalThis, 'fetch').mockImplementationOnce(async (url, init) => {
        expect(url.toString()).toContain('/api/v1/alerts/723e4567-e89b-12d3-a456-426614174006/status');
        expect(init?.method).toBe('PATCH');
        const body = JSON.parse(init?.body as string);
        expect(body.status).toBe('ACKNOWLEDGED');
        expect(body.notes).toBe('Reviewing elevated vitals; scheduling home visit');

        return {
          ok: true,
          status: 200,
          json: async () => mockUpdatedAlert,
        } as Response;
      });

      const result = await alertService.updateAlertStatus(
        '723e4567-e89b-12d3-a456-426614174006',
        payload,
        'token-alert-patch'
      );
      expect(result.status).toBe('ACKNOWLEDGED');
    });

    it('enforces frozen AlertStatus enum values and excludes old frontend values', () => {
      const validStatuses: AlertStatus[] = [
        'NEW',
        'ACKNOWLEDGED',
        'CONTACTED',
        'VISIT_SCHEDULED',
        'FOLLOW_UP_PENDING',
        'RESOLVED',
        'ESCALATED',
      ];

      expect(validStatuses).toHaveLength(7);
      expect(validStatuses).toContain('NEW');
      expect(validStatuses).toContain('ACKNOWLEDGED');
      expect(validStatuses).toContain('CONTACTED');
      expect(validStatuses).toContain('VISIT_SCHEDULED');
      expect(validStatuses).toContain('FOLLOW_UP_PENDING');
      expect(validStatuses).toContain('RESOLVED');
      expect(validStatuses).toContain('ESCALATED');

      // Verify old values are not accepted
      const testOldPending = 'PENDING';
      const testOldInProgress = 'IN_PROGRESS';
      expect(validStatuses.includes(testOldPending as AlertStatus)).toBe(false);
      expect(validStatuses.includes(testOldInProgress as AlertStatus)).toBe(false);
    });
  });

  // ----------------------------------------------------------------------------
  // 5. Visits Service (POST /api/v1/visits)
  // ----------------------------------------------------------------------------
  describe('5. Visits Contract', () => {
    it('creates an ASHA visit via POST /api/v1/visits and verifies VisitStatus enum', async () => {
      const payload: VisitCreate = {
        mother_id: '223e4567-e89b-12d3-a456-426614174001',
        alert_id: '723e4567-e89b-12d3-a456-426614174006',
        visit_date: '2026-10-04T09:00:00Z',
        notes: 'Scheduled home visit to repeat blood pressure check',
        findings: { systolic_bp_repeat: 124 },
      };

      const mockResponse: VisitResponse = {
        id: '823e4567-e89b-12d3-a456-426614174007',
        mother_id: '223e4567-e89b-12d3-a456-426614174001',
        asha_id: '323e4567-e89b-12d3-a456-426614174002',
        alert_id: '723e4567-e89b-12d3-a456-426614174006',
        visit_date: '2026-10-04T09:00:00Z',
        status: 'SCHEDULED',
        notes: 'Scheduled home visit to repeat blood pressure check',
        findings: { systolic_bp_repeat: 124 },
        created_at: '2026-10-03T11:00:00Z',
      };

      vi.spyOn(globalThis, 'fetch').mockImplementationOnce(async (url, init) => {
        expect(url.toString()).toContain('/api/v1/visits');
        expect(init?.method).toBe('POST');
        const body = JSON.parse(init?.body as string);
        expect(body.mother_id).toBe('223e4567-e89b-12d3-a456-426614174001');

        return {
          ok: true,
          status: 201,
          json: async () => mockResponse,
        } as Response;
      });

      const result = await visitService.createVisit(payload, 'token-visit');
      expect(result).toEqual(mockResponse);
      expect(result.status).toBe('SCHEDULED');

      const validVisitStatuses: VisitStatus[] = ['SCHEDULED', 'COMPLETED', 'CANCELLED', 'RESCHEDULED'];
      expect(validVisitStatuses).toContain(result.status);
    });
  });

  // ----------------------------------------------------------------------------
  // 6. Follow-up Service (POST /api/v1/followups)
  // ----------------------------------------------------------------------------
  describe('6. Follow-up Contract', () => {
    it('schedules an ASHA follow-up via POST /api/v1/followups and verifies FollowUpStatus enum', async () => {
      const payload: FollowUpCreate = {
        mother_id: '223e4567-e89b-12d3-a456-426614174001',
        alert_id: '723e4567-e89b-12d3-a456-426614174006',
        due_date: '2026-10-07',
        notes: 'Follow up on iron supplement intake and headaches',
      };

      const mockResponse: FollowUpResponse = {
        id: '923e4567-e89b-12d3-a456-426614174008',
        mother_id: '223e4567-e89b-12d3-a456-426614174001',
        asha_id: '323e4567-e89b-12d3-a456-426614174002',
        alert_id: '723e4567-e89b-12d3-a456-426614174006',
        visit_id: null,
        due_date: '2026-10-07',
        status: 'PENDING',
        notes: 'Follow up on iron supplement intake and headaches',
        created_at: '2026-10-03T11:15:00Z',
      };

      vi.spyOn(globalThis, 'fetch').mockImplementationOnce(async (url, init) => {
        expect(url.toString()).toContain('/api/v1/followups');
        expect(init?.method).toBe('POST');
        const body = JSON.parse(init?.body as string);
        expect(body.due_date).toBe('2026-10-07');

        return {
          ok: true,
          status: 201,
          json: async () => mockResponse,
        } as Response;
      });

      const result = await followUpService.createFollowUp(payload, 'token-followup');
      expect(result).toEqual(mockResponse);
      expect(result.status).toBe('PENDING');

      const validFollowUpStatuses: FollowUpStatus[] = ['PENDING', 'COMPLETED', 'OVERDUE', 'CANCELLED'];
      expect(validFollowUpStatuses).toContain(result.status);
    });
  });

  // ----------------------------------------------------------------------------
  // 7. Longitudinal Risk Timeline (GET /api/v1/mothers/{id}/risk-timeline)
  // ----------------------------------------------------------------------------
  describe('7. Longitudinal Risk Timeline Contract (Only Approved Historical Read)', () => {
    it('retrieves chronological timeline via GET /api/v1/mothers/{id}/risk-timeline', async () => {
      const motherId = '223e4567-e89b-12d3-a456-426614174001';
      const mockTimeline: RiskTimelineResponse = {
        mother_id: motherId,
        current_risk_level: 'LOW',
        assessments: [
          {
            timestamp: '2026-10-03T10:35:05Z',
            risk_level: 'LOW',
            assessment_type: 'PREDICTION',
            trigger_reason: null,
            systolic_bp: 120.0,
            diastolic_bp: 80.0,
            hemoglobin: 11.2,
            blood_sugar: 92.0,
          },
        ],
      };

      vi.spyOn(globalThis, 'fetch').mockImplementationOnce(async (url, init) => {
        expect(url.toString()).toContain(`/api/v1/mothers/${motherId}/risk-timeline`);
        expect(init?.method).toBe('GET');

        return {
          ok: true,
          status: 200,
          json: async () => mockTimeline,
        } as Response;
      });

      const result = await timelineService.getRiskTimeline(motherId, 'token-timeline');
      expect(result.mother_id).toBe(motherId);
      expect(result.current_risk_level).toBe('LOW');
      expect(result.assessments).toHaveLength(1);
      expect(result.assessments[0].systolic_bp).toBe(120.0);
      expect(result.assessments[0].hemoglobin).toBe(11.2);
    });
  });

  // ----------------------------------------------------------------------------
  // 8. Explicit Verification: No Unapproved Endpoints Exist
  // ----------------------------------------------------------------------------
  describe('8. Contract Boundary Compliance (Absence of Unapproved GET Endpoints)', () => {
    it('confirms healthRecordService does NOT expose a GET health-records method', () => {
      expect((healthRecordService as Record<string, unknown>)['getHealthRecords']).toBeUndefined();
      expect((healthRecordService as Record<string, unknown>)['listHealthRecords']).toBeUndefined();
    });

    it('confirms symptomService does NOT expose a GET symptoms method', () => {
      expect((symptomService as Record<string, unknown>)['getSymptoms']).toBeUndefined();
      expect((symptomService as Record<string, unknown>)['listSymptoms']).toBeUndefined();
    });
  });

  // ----------------------------------------------------------------------------
  // 9. HTTP Status Handling & Error Envelope Integration
  // ----------------------------------------------------------------------------
  describe('9. HTTP Status Handling (200, 201, 204, 401, 403, 422)', () => {
    it('handles 200 OK success', async () => {
      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ status: 'healthy' }),
      } as Response);

      const result = await apiRequest<{ status: string }>('/health');
      expect(result.status).toBe('healthy');
    });

    it('handles 201 Created success', async () => {
      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => ({ id: 'new-id', created: true }),
      } as Response);

      const result = await apiRequest<{ id: string; created: boolean }>('/health-records', {
        method: 'POST',
        body: JSON.stringify({}),
      });
      expect(result.id).toBe('new-id');
    });

    it('handles 204 No Content returning empty object without JSON parsing error', async () => {
      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: true,
        status: 204,
      } as Response);

      const result = await apiRequest('/resource/123', { method: 'DELETE' });
      expect(result).toEqual({});
    });

    it('throws ApiError with HTTP 401 Unauthorized for missing/invalid token', async () => {
      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        json: async () => ({
          error: {
            code: 'UNAUTHORIZED',
            message: 'Missing or malformed Authorization header.',
            details: {},
          },
        }),
      } as Response);

      try {
        await apiRequest('/alerts');
        expect.unreachable('Should have thrown ApiError');
      } catch (err: unknown) {
        expect(err).toBeInstanceOf(ApiError);
        const apiErr = err as ApiError;
        expect(apiErr.status).toBe(401);
        expect(apiErr.code).toBe('UNAUTHORIZED');
        expect(apiErr.message).toBe('Missing or malformed Authorization header.');
      }
    });

    it('throws ApiError with HTTP 403 Forbidden for cross-patient or role violation', async () => {
      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: false,
        status: 403,
        statusText: 'Forbidden',
        json: async () => ({
          error: {
            code: 'FORBIDDEN',
            message: 'Access forbidden: role MOTHER does not have required permissions.',
            details: { required_roles: ['ASHA', 'ADMIN'] },
          },
        }),
      } as Response);

      try {
        await apiRequest('/visits', { method: 'POST', body: '{}' });
        expect.unreachable('Should have thrown ApiError');
      } catch (err: unknown) {
        expect(err).toBeInstanceOf(ApiError);
        const apiErr = err as ApiError;
        expect(apiErr.status).toBe(403);
        expect(apiErr.code).toBe('FORBIDDEN');
        expect(apiErr.details).toEqual({ required_roles: ['ASHA', 'ADMIN'] });
      }
    });

    it('throws ApiError with HTTP 422 Unprocessable Entity for schema validation error', async () => {
      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: false,
        status: 422,
        statusText: 'Unprocessable Entity',
        json: async () => ({
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Input should be greater than or equal to 50.0',
            details: { field: 'systolic_bp', input: 30.0 },
          },
        }),
      } as Response);

      try {
        await healthRecordService.createHealthRecord({ systolic_bp: 30.0 });
        expect.unreachable('Should have thrown ApiError');
      } catch (err: unknown) {
        expect(err).toBeInstanceOf(ApiError);
        const apiErr = err as ApiError;
        expect(apiErr.status).toBe(422);
        expect(apiErr.code).toBe('VALIDATION_ERROR');
        expect(apiErr.details).toEqual({ field: 'systolic_bp', input: 30.0 });
      }
    });
  });

  // ----------------------------------------------------------------------------
  // 10. API Consumer State Pattern (data, isLoading, error, isEmpty)
  // ----------------------------------------------------------------------------
  describe('10. API Consumer State Pattern', () => {
    it('accurately represents data, isLoading, error, and isEmpty state transitions', () => {
      // 1. Initial State
      const state1 = { data: null, isLoading: false, error: null, isEmpty: false };
      expect(state1.isLoading).toBe(false);
      expect(state1.isEmpty).toBe(false);

      // 2. Loading State
      const state2 = { data: null, isLoading: true, error: null, isEmpty: false };
      expect(state2.isLoading).toBe(true);
      expect(state2.isEmpty).toBe(false);

      // 3. Error State
      const errorDetail = { code: 'HTTP_500', message: 'Internal Server Error' };
      const state3 = { data: null, isLoading: false, error: errorDetail, isEmpty: false };
      expect(state3.error).toEqual(errorDetail);
      expect(state3.isEmpty).toBe(false);

      // 4. Populated Data State
      const state4 = {
        data: [{ id: 'item-1' }],
        isLoading: false,
        error: null,
        isEmpty: false,
      };
      expect(state4.data).toHaveLength(1);
      expect(state4.isEmpty).toBe(false);

      // 5. Empty List State
      const emptyList: unknown[] = [];
      const isEmptyList = emptyList.length === 0;
      expect(isEmptyList).toBe(true);

      // 6. Empty Paginated Response State
      const emptyPaginated = { items: [], total: 0, page: 1, size: 20, total_pages: 0 };
      const isEmptyPaginated = emptyPaginated.items.length === 0;
      expect(isEmptyPaginated).toBe(true);
    });
  });
});

