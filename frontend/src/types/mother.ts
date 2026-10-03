/**
 * Baseline Mother types for MaternAI portal.
 * Risk levels correspond to the 3 ML risk tiers: LOW, MEDIUM, HIGH.
 */

export type MaternalRiskLevel = 'LOW' | 'MEDIUM' | 'HIGH';

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

export interface VitalMeasurements {
  systolicBp?: number;
  diastolicBp?: number;
  bloodGlucose?: number;
  bodyTemperature?: number;
  heartRate?: number;
}
