import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../auth';
import { Card, Badge, Button, AlertBanner } from '../../components/common';
import { alertService } from '../../services/alertService';
import type { AlertResponse } from '../../types/asha';
import { formatDate } from '../../utils/formatters';

export const AshaDashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [alerts, setAlerts] = useState<AlertResponse[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState<number>(0);

  useEffect(() => {
    let isMounted = true;

    alertService
      .listAlerts(1, 50)
      .then((res) => {
        if (isMounted) {
          setAlerts(res.items || []);
        }
      })
      .catch((err: unknown) => {
        if (isMounted) {
          const msg = err instanceof Error ? err.message : 'Failed to load ASHA coordination alerts.';
          setError(msg);
        }
      })
      .finally(() => {
        if (isMounted) {
          setIsLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [refreshKey]);

  const handleRefresh = useCallback(() => {
    setIsLoading(true);
    setError(null);
    setRefreshKey((k) => k + 1);
  }, []);

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

  const highPriorityAlerts = alerts.filter(
    (a) =>
      (a.severity === 'HIGH' || a.severity === 'CRITICAL' || a.status === 'ESCALATED') &&
      a.status !== 'RESOLVED'
  );

  return (
    <div className="portal-dashboard asha-dashboard" role="region" aria-labelledby="asha-dash-title">
      <header className="dashboard-header">
        <div>
          <h1 id="asha-dash-title" className="dash-title">
            ASHA Care Coordinator: {user?.fullName || 'Care Coordinator'}
          </h1>
          <p className="dash-subtitle">
            Community Maternal Surveillance & Escalation Queue (Care Coordination & Escalation)
          </p>
        </div>
        <div className="header-actions">
          <Link to="/asha/alerts">
            <Button variant="danger">
              ⚠️ Review Alerts ({isLoading ? '...' : `${activeAlerts.length} Active`})
            </Button>
          </Link>
        </div>
      </header>

      {/* Case Metrics Grid */}
      <div className="metrics-grid">
        <div className="metric-card">
          <span className="metric-label">Active Cohort Mothers</span>
          <strong className="metric-value">
            {isLoading ? '...' : uniqueMothersCount}
          </strong>
        </div>
        <div className="metric-card alert-metric">
          <span className="metric-label">Pending Escalation Alerts</span>
          <strong className="metric-value text-danger">
            {isLoading ? '...' : pendingEscalations.length}
          </strong>
        </div>
        <div className="metric-card">
          <span className="metric-label">Visits Scheduled</span>
          <strong className="metric-value">
            {isLoading ? '...' : scheduledVisits.length}
          </strong>
        </div>
        <div className="metric-card">
          <span className="metric-label">Resolved Cases</span>
          <strong className="metric-value text-success">
            {isLoading ? '...' : resolvedAlerts.length}
          </strong>
        </div>
      </div>

      {error && (
        <div className="mt-4 space-y-2">
          <AlertBanner type="danger" message={error} />
          <Button variant="outline" size="sm" onClick={handleRefresh}>
            Retry Loading Dashboard
          </Button>
        </div>
      )}

      <div className="dashboard-grid mt-4">
        <Card
          title="High Priority Alerts"
          subtitle="Cases flagged by deterministic safety rules or high-risk ML predictions"
        >
          {isLoading ? (
            <div className="p-4 text-center text-muted" role="status">
              <div className="spinner mx-auto mb-2" />
              <p className="text-sm">Loading priority alerts...</p>
            </div>
          ) : highPriorityAlerts.length === 0 ? (
            <div className="p-4 text-center text-muted">
              <p className="text-sm font-semibold">No high-priority alerts in your sector.</p>
              <p className="text-xs">All active cases are currently within normal triage parameters.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {highPriorityAlerts.slice(0, 3).map((alert) => (
                <div
                  key={alert.id}
                  className="alert-item-row flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-2 border-b last:border-b-0"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <Badge
                        label={alert.severity}
                        variant={
                          alert.severity === 'CRITICAL'
                            ? 'critical'
                            : alert.severity === 'HIGH'
                            ? 'danger'
                            : 'warning'
                        }
                      />
                      <Badge label={alert.status} variant="neutral" />
                      <strong>
                        {alert.mother_name || `Mother (${alert.mother_id.slice(0, 8)}...)`}
                      </strong>
                    </div>
                    <p className="text-sm text-muted mt-1">
                      {alert.trigger_reason}
                    </p>
                    <span className="text-[11px] text-muted">
                      Reported: {formatDate(alert.created_at)}
                    </span>
                  </div>
                  <div className="flex gap-2">
                    <Link
                      to={`/asha/mothers/${alert.mother_id}/timeline`}
                      className="btn btn-outline btn-sm"
                    >
                      Timeline →
                    </Link>
                    <Link to="/asha/alerts" className="btn btn-outline btn-sm">
                      Triage →
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card title="Assigned Mothers Roster" subtitle="Maternal cohort under care">
          <p className="text-sm text-muted">
            Directly monitor vital recordings, overdue checkups, and delivery planning.
          </p>
          <div className="mt-3">
            <Link to="/asha/mothers" className="btn btn-secondary btn-sm">
              View Assigned Mothers Roster →
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
};
