/**
 * Safety Status Badge component.
 *
 * Displays the authoritative deterministic safety state from the backend SafetyEngine:
 * - CLEAR: Normal baseline safety state
 * - CONCERNING: Concerning clinical rule triggered
 * - EMERGENCY: Immediate escalation rule triggered
 *
 * CRITICAL SEPARATION:
 * Safety states (CLEAR / CONCERNING / EMERGENCY) are strictly separate from ML risk levels
 * (LOW / MEDIUM / HIGH). The frontend does not calculate or map between them.
 */

import React from 'react';
import type { SafetyStatus } from '../../types/ai';
import { Badge } from '../common';

export interface SafetyStatusBadgeProps {
  safetyState?: SafetyStatus | null;
  className?: string;
}

export const SafetyStatusBadge: React.FC<SafetyStatusBadgeProps> = ({
  safetyState,
  className = '',
}) => {
  if (!safetyState) {
    return null;
  }

  const getVariant = (state: SafetyStatus): 'success' | 'warning' | 'danger' => {
    switch (state) {
      case 'EMERGENCY':
        return 'danger';
      case 'CONCERNING':
        return 'warning';
      case 'CLEAR':
      default:
        return 'success';
    }
  };

  return (
    <Badge
      label={`SAFETY STATE: ${safetyState}`}
      variant={getVariant(safetyState)}
      className={`safety-status-badge font-semibold ${className}`}
    />
  );
};
