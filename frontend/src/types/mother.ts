/**
 * Maternal health, vitals, symptoms, predictions, and timeline types.
 * Strictly adheres to backend Pydantic schemas and docs/api_contracts.md.
 */

export type MaternalRiskLevel = 'LOW' | 'MEDIUM' | 'HIGH';

// ------------------------------------------------------------------------------
// Mother Profile Contracts (GET /api/v1/mothers/me)
// ------------------------------------------------------------------------------
export interface MotherProfileResponse {
  id: string;
  user_id: string;
  full_name: string;
  date_of_birth?: string | null;
  age_years?: number | null;
  gestational_age_weeks?: number | null;
  expected_due_date?: string | null;
  assigned_asha_id?: string | null;
  last_risk_level?: MaternalRiskLevel | null;
  phone?: string | null;
  created_at: string;
}

// Phase 1 backwards-compatibility alias
export interface MotherProfile {
  id: string;
  userId: string;
  fullName: string;
  age?: number;
  gestationalAgeWeeks?: number;
  assignedAshaId?: string;
  lastRiskLevel?: MaternalRiskLevel;
  phone?: string;
  createdAt?: string;
}

// ------------------------------------------------------------------------------
// Health Records Contracts (POST /api/v1/health-records)
// ------------------------------------------------------------------------------
export interface HealthRecordCreate {
  pregnancy_week?: number | null;
  systolic_bp?: number | null;
  diastolic_bp?: number | null;
  blood_sugar?: number | null;
  hemoglobin?: number | null;
  weight_kg?: number | null;
  body_temperature?: number | null;
  heart_rate?: number | null;
  recorded_at?: string | null;
}

export interface HealthRecordResponse {
  id: string;
  mother_id: string;
  pregnancy_week?: number | null;
  systolic_bp?: number | null;
  diastolic_bp?: number | null;
  blood_sugar?: number | null;
  hemoglobin?: number | null;
  weight_kg?: number | null;
  body_temperature?: number | null;
  heart_rate?: number | null;
  recorded_by?: string | null;
  recorded_at: string;
  created_at: string;
}

// Vital measurements helper type
export interface VitalMeasurements {
  systolic_bp?: number;
  diastolic_bp?: number;
  blood_sugar?: number;
  hemoglobin?: number;
  pregnancy_week?: number;
  weight_kg?: number;
  body_temperature?: number;
  heart_rate?: number;
  // Phase 1 camelCase aliases
  systolicBp?: number;
  diastolicBp?: number;
  bloodGlucose?: number;
  bodyTemperature?: number;
  heartRate?: number;
}

// ------------------------------------------------------------------------------
// Symptoms Contracts (POST /api/v1/symptoms)
// ------------------------------------------------------------------------------
export interface SymptomItem {
  symptom_code: string;
  severity: number;
  notes?: string | null;
}

export interface SymptomSubmission {
  health_record_id?: string | null;
  symptoms: SymptomItem[];
}

export interface SymptomResponse {
  id: string;
  mother_id: string;
  health_record_id?: string | null;
  symptom_code: string;
  severity: number;
  notes?: string | null;
  recorded_at: string;
  created_at: string;
}

// ------------------------------------------------------------------------------
// ML Predictions Contracts (POST /api/v1/predictions)
// ------------------------------------------------------------------------------
export interface MLRiskInput {
  age_years?: number | null;
  hemoglobin?: number | null;
  systolic_bp?: number | null;
  diastolic_bp?: number | null;
  blood_sugar?: number | null;
  weight_kg?: number | null;
  pregnancy_week?: number | null;
  symptom_features?: Record<string, number | boolean | string>;
}

export interface ContributingFactor {
  feature: string;
  direction: 'INCREASES_RISK' | 'DECREASES_RISK' | string;
  value?: unknown;
}

export interface PredictionRequest {
  health_record_id?: string | null;
  features?: MLRiskInput | null;
}

export interface PredictionResponse {
  id: string;
  mother_id: string;
  health_record_id?: string | null;
  risk_level: MaternalRiskLevel;
  model_score?: number | null;
  model_version: string;
  feature_schema_version: string;
  contributing_factors: ContributingFactor[];
  created_at: string;
}

// ------------------------------------------------------------------------------
// Longitudinal Risk Timeline Contracts (GET /api/v1/mothers/{id}/risk-timeline)
// ------------------------------------------------------------------------------
export interface RiskTimelinePoint {
  timestamp: string;
  risk_level: MaternalRiskLevel;
  assessment_type: string;
  trigger_reason?: string | null;
  systolic_bp?: number | null;
  diastolic_bp?: number | null;
  hemoglobin?: number | null;
  blood_sugar?: number | null;
}

export interface RiskTimelineResponse {
  mother_id: string;
  current_risk_level?: MaternalRiskLevel | null;
  assessments: RiskTimelinePoint[];
}
