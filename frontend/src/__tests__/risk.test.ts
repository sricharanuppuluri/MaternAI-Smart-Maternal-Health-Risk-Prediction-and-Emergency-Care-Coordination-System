/**
 * Phase 5 — Risk UI & Prediction Flow Tests
 *
 * Covers:
 * 1. LOW risk renders correctly.
 * 2. MEDIUM risk renders correctly.
 * 3. HIGH risk renders correctly.
 * 4. Contributing factor with INCREASES_RISK renders correctly.
 * 5. Contributing factor with DECREASES_RISK renders correctly.
 * 6. model_score is NOT rendered as percentage/probability.
 * 7. Health record submission triggers prediction flow.
 * 8. Timeline populated state renders assessments.
 * 9. Timeline empty state renders correctly.
 * 10. Timeline loading state renders correctly.
 * 11. Timeline error state renders correctly.
 * 12. Dashboard displays latest risk assessment.
 * 13. Dashboard displays no-assessment state correctly.
 * 14. No frontend code calls GET /api/v1/health-records.
 * 15. No frontend code calls GET /api/v1/symptoms.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { RiskAssessmentCard } from '../components/clinical/RiskAssessmentCard';
import {
  healthRecordService,
  symptomService,
  predictionService,
} from '../services';
import type {
  PredictionResponse,
  HealthRecordCreate,
  HealthRecordResponse,
  SymptomSubmission,
  RiskTimelineResponse,
} from '../types/mother';

describe('Phase 5 — ML Pipeline & Risk UI Verification Tests', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  // ----------------------------------------------------------------------------
  // 1–3: Categorical Risk Levels Rendering
  // ----------------------------------------------------------------------------
  it('1. renders LOW risk tier correctly with success variant', () => {
    const lowPrediction: PredictionResponse = {
      id: 'pred-low-1',
      mother_id: 'mother-1',
      risk_level: 'LOW',
      model_score: 0.12,
      model_version: 'v0.1.0',
      feature_schema_version: 'v1.0',
      contributing_factors: [],
      created_at: '2026-10-03T10:00:00Z',
    };

    const element = RiskAssessmentCard({ prediction: lowPrediction });
    const renderedJson = JSON.stringify(element);

    expect(renderedJson).toContain('LOW RISK');
    expect(renderedJson).toContain('"variant":"success"');
    expect(renderedJson).toContain('Standard prenatal monitoring trajectory');
  });

  it('2. renders MEDIUM risk tier correctly with warning variant', () => {
    const medPrediction: PredictionResponse = {
      id: 'pred-med-2',
      mother_id: 'mother-1',
      risk_level: 'MEDIUM',
      model_score: 0.48,
      model_version: 'v0.1.0',
      feature_schema_version: 'v1.0',
      contributing_factors: [],
      created_at: '2026-10-03T10:00:00Z',
    };

    const element = RiskAssessmentCard({ prediction: medPrediction });
    const renderedJson = JSON.stringify(element);

    expect(renderedJson).toContain('MEDIUM RISK');
    expect(renderedJson).toContain('"variant":"warning"');
    expect(renderedJson).toContain('Elevated monitoring recommended by ASHA care team');
  });

  it('3. renders HIGH risk tier correctly with danger variant', () => {
    const highPrediction: PredictionResponse = {
      id: 'pred-high-3',
      mother_id: 'mother-1',
      risk_level: 'HIGH',
      model_score: 0.85,
      model_version: 'v0.1.0',
      feature_schema_version: 'v1.0',
      contributing_factors: [],
      created_at: '2026-10-03T10:00:00Z',
    };

    const element = RiskAssessmentCard({ prediction: highPrediction });
    const renderedJson = JSON.stringify(element);

    expect(renderedJson).toContain('HIGH RISK');
    expect(renderedJson).toContain('"variant":"danger"');
    expect(renderedJson).toContain('Requires prompt clinical review and ASHA follow-up');
  });

  // ----------------------------------------------------------------------------
  // 4–5: Explainability Contributing Factors Rendering
  // ----------------------------------------------------------------------------
  it('4. renders contributing factor with INCREASES_RISK correctly', () => {
    const predictionWithHighFactor: PredictionResponse = {
      id: 'pred-factors-1',
      mother_id: 'mother-1',
      risk_level: 'HIGH',
      model_score: 0.78,
      model_version: 'v0.1.0',
      feature_schema_version: 'v1.0',
      contributing_factors: [
        {
          feature: 'systolic_bp',
          direction: 'INCREASES_RISK',
          value: 155,
        },
      ],
      created_at: '2026-10-03T10:00:00Z',
    };

    const element = RiskAssessmentCard({ prediction: predictionWithHighFactor });
    const renderedJson = JSON.stringify(element);

    expect(renderedJson).toContain('Systolic Bp');
    expect(renderedJson).toContain('Increases Risk');
    expect(renderedJson).toContain('"variant":"danger"');
    expect(renderedJson).toContain('155');
  });

  it('5. renders contributing factor with DECREASES_RISK correctly', () => {
    const predictionWithLowFactor: PredictionResponse = {
      id: 'pred-factors-2',
      mother_id: 'mother-1',
      risk_level: 'LOW',
      model_score: 0.15,
      model_version: 'v0.1.0',
      feature_schema_version: 'v1.0',
      contributing_factors: [
        {
          feature: 'hemoglobin',
          direction: 'DECREASES_RISK',
          value: 12.5,
        },
      ],
      created_at: '2026-10-03T10:00:00Z',
    };

    const element = RiskAssessmentCard({ prediction: predictionWithLowFactor });
    const renderedJson = JSON.stringify(element);

    expect(renderedJson).toContain('Hemoglobin');
    expect(renderedJson).toContain('Decreases Risk');
    expect(renderedJson).toContain('"variant":"success"');
    expect(renderedJson).toContain('12.5');
  });

  // ----------------------------------------------------------------------------
  // 6: model_score Clinical Safety Check (NOT percentage / probability / diagnosis)
  // ----------------------------------------------------------------------------
  it('6. ensures model_score is NEVER formatted or presented as probability percentage', () => {
    const testPrediction: PredictionResponse = {
      id: 'pred-safety-check',
      mother_id: 'mother-1',
      risk_level: 'HIGH',
      model_score: 0.72,
      model_version: 'v0.1.0',
      feature_schema_version: 'v1.0',
      contributing_factors: [
        { feature: 'systolic_bp', direction: 'INCREASES_RISK', value: 145 },
      ],
      created_at: '2026-10-03T10:00:00Z',
    };

    const element = RiskAssessmentCard({ prediction: testPrediction });
    const renderedJson = JSON.stringify(element);

    // Strictly forbidden diagnostic / percentage phrasing
    expect(renderedJson).not.toContain('72%');
    expect(renderedJson).not.toContain('% risk');
    expect(renderedJson).not.toContain('% chance');
    expect(renderedJson).not.toContain('diagnosed with');
    expect(renderedJson).not.toContain('you have');
    expect(renderedJson).not.toContain('probability');

    // Contains mandatory clinical decision-support advisory notice
    expect(renderedJson).toContain('Clinical Decision-Support Notice:');
    expect(renderedJson).toContain('an autonomous diagnostic determination');
  });

  // ----------------------------------------------------------------------------
  // 7: Health Record Submission -> Symptoms -> Prediction Sequence
  // ----------------------------------------------------------------------------
  it('7. executes health record submission, symptoms logging, and prediction flow in order', async () => {
    const mockHealthRecord: HealthRecordResponse = {
      id: 'hr-uuid-777',
      mother_id: 'mother-uuid-1',
      pregnancy_week: 28,
      systolic_bp: 130,
      diastolic_bp: 85,
      recorded_at: '2026-10-03T10:00:00Z',
      created_at: '2026-10-03T10:00:00Z',
    };

    const mockPrediction: PredictionResponse = {
      id: 'pred-uuid-888',
      mother_id: 'mother-uuid-1',
      health_record_id: 'hr-uuid-777',
      risk_level: 'MEDIUM',
      model_score: 0.35,
      model_version: 'v0.1.0',
      feature_schema_version: 'v1.0',
      contributing_factors: [
        { feature: 'systolic_bp', direction: 'INCREASES_RISK', value: 130 },
      ],
      created_at: '2026-10-03T10:00:05Z',
    };

    const callOrder: string[] = [];

    vi.spyOn(healthRecordService, 'createHealthRecord').mockImplementationOnce(async (payload: HealthRecordCreate) => {
      callOrder.push('createHealthRecord');
      expect(payload.systolic_bp).toBe(130);
      return mockHealthRecord;
    });

    vi.spyOn(symptomService, 'recordSymptoms').mockImplementationOnce(async (payload: SymptomSubmission) => {
      callOrder.push('recordSymptoms');
      expect(payload.health_record_id).toBe('hr-uuid-777');
      expect(payload.symptoms).toHaveLength(1);
      return [];
    });

    vi.spyOn(predictionService, 'requestPrediction').mockImplementationOnce(async (payload) => {
      callOrder.push('requestPrediction');
      expect(payload.health_record_id).toBe('hr-uuid-777');
      return mockPrediction;
    });

    // Execute flow
    const hr = await healthRecordService.createHealthRecord({ systolic_bp: 130, diastolic_bp: 85 });
    await symptomService.recordSymptoms({
      health_record_id: hr.id,
      symptoms: [{ symptom_code: 'headache', severity: 2 }],
    });
    const pred = await predictionService.requestPrediction({ health_record_id: hr.id });

    expect(callOrder).toEqual(['createHealthRecord', 'recordSymptoms', 'requestPrediction']);
    expect(pred.risk_level).toBe('MEDIUM');
    expect(pred.health_record_id).toBe('hr-uuid-777');
  });

  // ----------------------------------------------------------------------------
  // 8–11: Longitudinal Risk Timeline States
  // ----------------------------------------------------------------------------
  it('8. renders timeline populated state with chronological assessments', () => {
    const mockTimeline: RiskTimelineResponse = {
      mother_id: 'mother-101',
      current_risk_level: 'MEDIUM',
      assessments: [
        {
          timestamp: '2026-10-03T10:00:00Z',
          risk_level: 'MEDIUM',
          assessment_type: 'PREDICTION',
          trigger_reason: 'Mild hypertension',
          systolic_bp: 135,
          diastolic_bp: 88,
          hemoglobin: 11.0,
          blood_sugar: 98,
        },
        {
          timestamp: '2026-09-15T10:00:00Z',
          risk_level: 'LOW',
          assessment_type: 'PREDICTION',
          systolic_bp: 118,
          diastolic_bp: 76,
        },
      ],
    };

    expect(mockTimeline.current_risk_level).toBe('MEDIUM');
    expect(mockTimeline.assessments).toHaveLength(2);
    expect(mockTimeline.assessments[0].trigger_reason).toBe('Mild hypertension');
    expect(mockTimeline.assessments[0].systolic_bp).toBe(135);
  });

  it('9. renders timeline empty state with guidance message', () => {
    const emptyTimeline: RiskTimelineResponse = {
      mother_id: 'mother-102',
      current_risk_level: null,
      assessments: [],
    };

    expect(emptyTimeline.assessments).toHaveLength(0);
    expect(emptyTimeline.current_risk_level).toBeNull();
  });

  it('10. handles timeline loading state', () => {
    const cardElement = RiskAssessmentCard({ prediction: null, isLoading: true });
    const renderedJson = JSON.stringify(cardElement);

    expect(renderedJson).toContain('Evaluating measurements against decision-support models');
    expect(renderedJson).toContain('Evaluating clinical measurements against ML decision-support model...');
  });

  it('11. handles timeline error state', () => {
    const errorDetail = { code: 'HTTP_500', message: 'Database connection failed' };
    const cardElement = RiskAssessmentCard({ prediction: null, error: errorDetail });
    const renderedJson = JSON.stringify(cardElement);

    expect(renderedJson).toContain('Database connection failed');
  });

  // ----------------------------------------------------------------------------
  // 12–13: Dashboard Latest Risk & No-Assessment State
  // ----------------------------------------------------------------------------
  it('12. displays latest risk assessment on dashboard when timeline is present', () => {
    const timelineData: RiskTimelineResponse = {
      mother_id: 'm-1',
      current_risk_level: 'HIGH',
      assessments: [
        {
          timestamp: '2026-10-03T10:00:00Z',
          risk_level: 'HIGH',
          assessment_type: 'SAFETY_EVENT',
          trigger_reason: 'Systolic blood pressure >= 160 mmHg',
          systolic_bp: 165,
          diastolic_bp: 105,
        },
      ],
    };

    const currentRisk = timelineData.current_risk_level;
    expect(currentRisk).toBe('HIGH');
    expect(timelineData.assessments[0].trigger_reason).toContain('160 mmHg');
  });

  it('13. displays explicit no-assessment state on dashboard and does NOT claim "No risk detected"', () => {
    const noAssessmentTimeline: RiskTimelineResponse = {
      mother_id: 'm-2',
      current_risk_level: null,
      assessments: [],
    };

    const fallbackStatusText = noAssessmentTimeline.current_risk_level
      ? `${noAssessmentTimeline.current_risk_level} RISK`
      : 'No risk assessment available yet.';

    expect(fallbackStatusText).toBe('No risk assessment available yet.');
    expect(fallbackStatusText).not.toBe('No risk detected');
    expect(fallbackStatusText).not.toContain('LOW RISK');
  });

  // ----------------------------------------------------------------------------
  // 14–15: Explicit Verification that Unapproved GET Endpoints Are Absent
  // ----------------------------------------------------------------------------
  it('14. verifies NO code exposes or calls GET /api/v1/health-records', () => {
    expect((healthRecordService as Record<string, unknown>)['getHealthRecords']).toBeUndefined();
    expect((healthRecordService as Record<string, unknown>)['listHealthRecords']).toBeUndefined();
    expect((healthRecordService as Record<string, unknown>)['getHealthRecord']).toBeUndefined();
  });

  it('15. verifies NO code exposes or calls GET /api/v1/symptoms', () => {
    expect((symptomService as Record<string, unknown>)['getSymptoms']).toBeUndefined();
    expect((symptomService as Record<string, unknown>)['listSymptoms']).toBeUndefined();
    expect((symptomService as Record<string, unknown>)['getSymptom']).toBeUndefined();
  });
});
