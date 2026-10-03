/**
 * Baseline ASHA types for MaternAI portal.
 */

export type AlertSeverity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
export type AlertStatus = 'PENDING' | 'ACKNOWLEDGED' | 'IN_PROGRESS' | 'RESOLVED';

export interface AshaProfile {
  id: string;
  userId: string;
  fullName: string;
  workerCode?: string;
  assignedVillage?: string;
  phone?: string;
  activeCasesCount?: number;
}

export interface AshaAlertSummary {
  id: string;
  motherId: string;
  motherName: string;
  severity: AlertSeverity;
  status: AlertStatus;
  triggerReason: string;
  createdAt: string;
}
