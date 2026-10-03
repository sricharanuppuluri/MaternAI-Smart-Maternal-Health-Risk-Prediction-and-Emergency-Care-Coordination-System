/**
 * Common formatting utilities for MaternAI.
 */

import type { MaternalRiskLevel } from '../types/mother';
import type { AlertSeverity } from '../types/asha';

export function formatDate(dateString?: string): string {
  if (!dateString) return '—';
  try {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    }).format(date);
  } catch {
    return dateString;
  }
}

export function getRiskBadgeClass(level?: MaternalRiskLevel): string {
  switch (level) {
    case 'HIGH':
      return 'badge-danger';
    case 'MEDIUM':
      return 'badge-warning';
    case 'LOW':
      return 'badge-success';
    default:
      return 'badge-neutral';
  }
}

export function getAlertBadgeClass(severity?: AlertSeverity): string {
  switch (severity) {
    case 'CRITICAL':
      return 'badge-critical';
    case 'HIGH':
      return 'badge-danger';
    case 'MEDIUM':
      return 'badge-warning';
    case 'LOW':
      return 'badge-info';
    default:
      return 'badge-neutral';
  }
}
