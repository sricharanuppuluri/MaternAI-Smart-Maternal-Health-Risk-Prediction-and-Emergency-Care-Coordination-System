/**
 * ASHA worker, alerts, visits, and follow-up types.
 * Strictly adheres to backend Pydantic schemas and docs/api_contracts.md.
 */

// ------------------------------------------------------------------------------
// Alert Enums & Contracts (GET /api/v1/alerts, PATCH /api/v1/alerts/{id}/status)
// ------------------------------------------------------------------------------
export type AlertSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type AlertStatus =
  | 'NEW'
  | 'ACKNOWLEDGED'
  | 'CONTACTED'
  | 'VISIT_SCHEDULED'
  | 'FOLLOW_UP_PENDING'
  | 'RESOLVED'
  | 'ESCALATED';

export interface AlertResponse {
  id: string;
  mother_id: string;
  mother_name?: string | null;
  asha_id?: string | null;
  severity: AlertSeverity;
  status: AlertStatus;
  trigger_reason: string;
  safety_event_id?: string | null;
  prediction_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AlertStatusUpdate {
  status: AlertStatus;
  notes?: string | null;
}

// Phase 1 UI summary helper
export interface AshaAlertSummary {
  id: string;
  motherId?: string;
  mother_id?: string;
  motherName?: string;
  mother_name?: string;
  severity: AlertSeverity;
  status: AlertStatus;
  triggerReason?: string;
  trigger_reason?: string;
  createdAt?: string;
  created_at?: string;
}

// ------------------------------------------------------------------------------
// Visits Contracts (POST /api/v1/visits)
// ------------------------------------------------------------------------------
export type VisitStatus = 'SCHEDULED' | 'COMPLETED' | 'CANCELLED' | 'RESCHEDULED';

export interface VisitCreate {
  mother_id: string;
  alert_id?: string | null;
  visit_date: string;
  notes?: string | null;
  findings?: Record<string, unknown>;
}

export interface VisitResponse {
  id: string;
  mother_id: string;
  asha_id: string;
  alert_id?: string | null;
  visit_date: string;
  status: VisitStatus;
  notes?: string | null;
  findings: Record<string, unknown>;
  created_at: string;
}

// ------------------------------------------------------------------------------
// Follow-up Contracts (POST /api/v1/followups)
// ------------------------------------------------------------------------------
export type FollowUpStatus = 'PENDING' | 'COMPLETED' | 'OVERDUE' | 'CANCELLED';

export interface FollowUpCreate {
  mother_id: string;
  alert_id?: string | null;
  visit_id?: string | null;
  due_date: string; // ISO Date YYYY-MM-DD
  notes?: string | null;
}

export interface FollowUpResponse {
  id: string;
  mother_id: string;
  asha_id: string;
  alert_id?: string | null;
  visit_id?: string | null;
  due_date: string;
  status: FollowUpStatus;
  notes?: string | null;
  created_at: string;
}

// ------------------------------------------------------------------------------
// ASHA Profile (Phase 1 Baseline)
// ------------------------------------------------------------------------------
export interface AshaProfile {
  id: string;
  userId: string;
  fullName: string;
  workerCode?: string;
  assignedVillage?: string;
  phone?: string;
  activeCasesCount?: number;
}
