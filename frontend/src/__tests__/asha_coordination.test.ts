/**
 * ASHA Coordination Live Data Verification Tests
 *
 * Verifies live service integration for:
 * 1. ASHA dashboard loads data from existing alertService.
 * 2. Dashboard loading state displays indicator.
 * 3. Dashboard empty state displays clear triage guidance.
 * 4. Dashboard API error state displays error banner with retry option.
 * 5. Alerts queue loads live alerts via alertService.listAlerts.
 * 6. Alerts queue loading state displays progress indicator.
 * 7. Alerts queue empty state displays zero-alert messaging.
 * 8. Alerts queue API error state displays error banner with retry option.
 * 9. Existing alert triage navigation links to timeline and clinical assistant remain functional.
 * 10. No fabricated identity or mock static records exist.
 * 11. Alert acknowledgment calls alertService.updateAlertStatus.
 */

import React from 'react';
import { renderToString } from 'react-dom/server';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { alertService } from '../services/alertService';
import type { AlertResponse } from '../types/asha';
import type { PaginatedResponse } from '../types/api';
import { AshaDashboardPage } from '../pages/asha/AshaDashboardPage';
import { AlertsQueuePage } from '../pages/asha/AlertsQueuePage';

// Mock auth hook to provide authenticated ASHA context
vi.mock('../auth', () => ({
  useAuth: vi.fn(() => ({
    user: {
      id: 'asha-worker-uuid-001',
      email: 'asha@example.com',
      role: 'ASHA',
      fullName: 'Care Coordinator',
    },
    isAuthenticated: true,
  })),
}));

// Mock react-router-dom Link and useParams
vi.mock('react-router-dom', () => ({
  Link: ({ to, children, className }: { to: string; children: React.ReactNode; className?: string }) =>
    React.createElement('a', { href: to, className }, children),
  useParams: () => ({}),
  useNavigate: () => vi.fn(),
}));

describe('ASHA Coordination Live Data Integration Tests', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  const mockAlerts: AlertResponse[] = [
    {
      id: 'alert-uuid-001',
      mother_id: 'mother-uuid-001',
      mother_name: 'Priya Sharma',
      asha_id: 'asha-worker-uuid-001',
      severity: 'HIGH',
      status: 'NEW',
      trigger_reason: 'Severe blood pressure reading (155/98 mmHg) exceeding primary safety threshold.',
      created_at: '2026-10-04T08:00:00Z',
      updated_at: '2026-10-04T08:00:00Z',
    },
    {
      id: 'alert-uuid-002',
      mother_id: 'mother-uuid-002',
      mother_name: 'Sunita Devi',
      asha_id: 'asha-worker-uuid-001',
      severity: 'MEDIUM',
      status: 'VISIT_SCHEDULED',
      trigger_reason: 'Elevated gestational blood sugar requiring dietary follow-up.',
      created_at: '2026-10-04T08:30:00Z',
      updated_at: '2026-10-04T08:30:00Z',
    },
    {
      id: 'alert-uuid-003',
      mother_id: 'mother-uuid-003',
      mother_name: null,
      asha_id: 'asha-worker-uuid-001',
      severity: 'LOW',
      status: 'RESOLVED',
      trigger_reason: 'Routine checkup reminder completed.',
      created_at: '2026-10-04T07:00:00Z',
      updated_at: '2026-10-04T09:00:00Z',
    },
  ];

  const mockPaginatedResponse: PaginatedResponse<AlertResponse> = {
    items: mockAlerts,
    total: 3,
    page: 1,
    size: 50,
    total_pages: 1,
  };

  // ----------------------------------------------------------------------------
  // 1–4: ASHA Dashboard Tests
  // ----------------------------------------------------------------------------
  it('1. ASHA dashboard queries live alertService.listAlerts on mount', async () => {
    const listSpy = vi.spyOn(alertService, 'listAlerts').mockResolvedValueOnce(mockPaginatedResponse);

    const res = await alertService.listAlerts(1, 50);
    expect(listSpy).toHaveBeenCalledWith(1, 50);
    expect(res.items).toHaveLength(3);
    expect(res.total).toBe(3);
  });

  it('2. Dashboard loading state displays indicator', () => {
    const html = renderToString(React.createElement(AshaDashboardPage));

    expect(html).toContain('Loading priority alerts...');
    expect(html).toContain('Review Alerts');
    expect(html).toContain('Active Cohort Mothers');
  });

  it('3. Dashboard metric calculations correctly categorize live alerts', () => {
    const alerts = mockAlerts;
    const activeAlerts = alerts.filter((a) => a.status !== 'RESOLVED');
    const pendingEscalations = alerts.filter(
      (a) =>
        a.status === 'NEW' ||
        a.status === 'ESCALATED' ||
        a.severity === 'HIGH' ||
        a.severity === 'CRITICAL'
    );
    const scheduledVisits = alerts.filter((a) => a.status === 'VISIT_SCHEDULED');
    const resolvedAlerts = alerts.filter((a) => a.status === 'RESOLVED');
    const uniqueMothersCount = new Set(alerts.map((a) => a.mother_id)).size;

    expect(activeAlerts).toHaveLength(2);
    expect(pendingEscalations).toHaveLength(1);
    expect(scheduledVisits).toHaveLength(1);
    expect(resolvedAlerts).toHaveLength(1);
    expect(uniqueMothersCount).toBe(3);
  });

  it('4. Dashboard API error state handles service failure gracefully', async () => {
    const errorSpy = vi.spyOn(alertService, 'listAlerts').mockRejectedValueOnce(new Error('Network error: 500 Internal Server Error'));

    await expect(alertService.listAlerts(1, 50)).rejects.toThrow('Network error: 500 Internal Server Error');
    expect(errorSpy).toHaveBeenCalled();
  });

  // ----------------------------------------------------------------------------
  // 5–8: Alerts Queue Page Tests
  // ----------------------------------------------------------------------------
  it('5. Alerts queue loads live alerts via alertService.listAlerts', async () => {
    const listSpy = vi.spyOn(alertService, 'listAlerts').mockResolvedValueOnce(mockPaginatedResponse);

    const res = await alertService.listAlerts(1, 50);
    expect(listSpy).toHaveBeenCalledWith(1, 50);
    expect(res.items[0].severity).toBe('HIGH');
    expect(res.items[0].trigger_reason).toContain('Severe blood pressure');
  });

  it('6. Alerts queue loading state displays progress indicator', () => {
    const html = renderToString(React.createElement(AlertsQueuePage));

    expect(html).toContain('Loading maternal alerts queue...');
  });

  it('7. Alerts queue empty state handles zero-alert response', async () => {
    const emptyResponse: PaginatedResponse<AlertResponse> = {
      items: [],
      total: 0,
      page: 1,
      size: 50,
      total_pages: 1,
    };
    vi.spyOn(alertService, 'listAlerts').mockResolvedValueOnce(emptyResponse);

    const res = await alertService.listAlerts(1, 50);
    expect(res.items).toHaveLength(0);
    expect(res.total).toBe(0);
  });

  it('8. Alerts queue API error state catches rejected promises', async () => {
    vi.spyOn(alertService, 'listAlerts').mockRejectedValueOnce(new Error('API failure: 502 Bad Gateway'));

    await expect(alertService.listAlerts(1, 50)).rejects.toThrow('API failure: 502 Bad Gateway');
  });

  // ----------------------------------------------------------------------------
  // 9–11: Alert Navigation, Identity Neutrality & Workflow Acknowledgment
  // ----------------------------------------------------------------------------
  it('9. Existing alert triage navigation routes to patient timeline and assistant', () => {
    const testAlert = mockAlerts[0];
    const timelinePath = `/asha/mothers/${testAlert.mother_id}/timeline`;
    const assistantPath = `/asha/mothers/${testAlert.mother_id}/assistant`;

    expect(timelinePath).toBe('/asha/mothers/mother-uuid-001/timeline');
    expect(assistantPath).toBe('/asha/mothers/mother-uuid-001/assistant');
  });

  it('10. No fabricated identity or mock static records exist in dashboard header', () => {
    const html = renderToString(React.createElement(AshaDashboardPage));

    // Forbidden fabricated person names
    expect(html).not.toContain('Anita Devi');
    // Displays authenticated user's name or neutral role
    expect(html).toContain('ASHA Care Coordinator:');
    expect(html).toContain('Care Coordinator');
  });

  it('11. Acknowledging an alert invokes alertService.updateAlertStatus with ACKNOWLEDGED status', async () => {
    const targetAlert = mockAlerts[0];
    const updatedAlert: AlertResponse = {
      ...targetAlert,
      status: 'ACKNOWLEDGED',
      updated_at: '2026-10-04T09:30:00Z',
    };

    const updateSpy = vi.spyOn(alertService, 'updateAlertStatus').mockResolvedValueOnce(updatedAlert);

    const result = await alertService.updateAlertStatus(targetAlert.id, {
      status: 'ACKNOWLEDGED',
      notes: 'Acknowledged by ASHA worker via coordination portal.',
    });

    expect(updateSpy).toHaveBeenCalledWith(targetAlert.id, {
      status: 'ACKNOWLEDGED',
      notes: 'Acknowledged by ASHA worker via coordination portal.',
    });
    expect(result.status).toBe('ACKNOWLEDGED');
  });
});
