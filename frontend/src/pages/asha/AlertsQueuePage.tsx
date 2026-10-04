import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Card, Badge, Button, AlertBanner } from '../../components/common';
import { alertService } from '../../services/alertService';
import type { AlertResponse } from '../../types/asha';
import { formatDate } from '../../utils/formatters';

export const AlertsQueuePage: React.FC = () => {
  const [alerts, setAlerts] = useState<AlertResponse[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [updatingAlertId, setUpdatingAlertId] = useState<string | null>(null);
  const [actionSuccessMessage, setActionSuccessMessage] = useState<string | null>(null);
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
          const msg = err instanceof Error ? err.message : 'Unable to load alerts queue.';
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

  const handleAcknowledge = async (alertId: string) => {
    setUpdatingAlertId(alertId);
    setActionSuccessMessage(null);
    try {
      const updated = await alertService.updateAlertStatus(alertId, {
        status: 'ACKNOWLEDGED',
        notes: 'Acknowledged by ASHA worker via coordination portal.',
      });
      setAlerts((prev) => prev.map((a) => (a.id === alertId ? updated : a)));
      setActionSuccessMessage(`Case ${alertId.slice(0, 8)} successfully acknowledged.`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to update alert status.';
      setError(msg);
    } finally {
      setUpdatingAlertId(null);
    }
  };

  const getSeverityVariant = (severity: string): 'danger' | 'warning' | 'info' | 'critical' | 'neutral' => {
    switch (severity) {
      case 'CRITICAL':
        return 'critical';
      case 'HIGH':
        return 'danger';
      case 'MEDIUM':
        return 'warning';
      case 'LOW':
        return 'info';
      default:
        return 'neutral';
    }
  };

  return (
    <div className="portal-page alerts-queue-page" role="region" aria-labelledby="alerts-title">
      <header className="page-header flex flex-col md:flex-row md:items-center justify-between gap-3 mb-4">
        <div>
          <h1 id="alerts-title" className="page-title">ASHA Escalation & Alert Queue</h1>
          <p className="page-subtitle">
            Triage and prioritize acute maternal risks triggered by safety engine thresholds or ML risk predictions.
          </p>
        </div>
        <div className="header-actions">
          <Button variant="outline" size="sm" onClick={handleRefresh} disabled={isLoading}>
            ↻ Refresh Queue
          </Button>
        </div>
      </header>

      {actionSuccessMessage && (
        <div className="mb-4">
          <AlertBanner
            type="success"
            message={actionSuccessMessage}
            onDismiss={() => setActionSuccessMessage(null)}
          />
        </div>
      )}

      {error && (
        <div className="mb-4 space-y-2">
          <AlertBanner type="danger" message={error} onDismiss={() => setError(null)} />
          <Button variant="outline" size="sm" onClick={handleRefresh}>
            Retry Loading
          </Button>
        </div>
      )}

      <Card title="Active Urgent Alerts" subtitle="Prioritized by clinical severity">
        {isLoading ? (
          <div className="p-8 text-center text-muted" role="status" aria-live="polite">
            <div className="spinner mx-auto mb-2" />
            <p className="font-semibold">Loading maternal alerts queue...</p>
          </div>
        ) : alerts.length === 0 ? (
          <div className="p-8 text-center text-muted" role="status">
            <p className="font-semibold text-base">No active escalation alerts found.</p>
            <p className="text-sm">The maternal surveillance queue for your sector is currently clear.</p>
          </div>
        ) : (
          <div className="alerts-list space-y-4">
            {alerts.map((alert) => (
              <div key={alert.id} className="alert-card-item p-4 border rounded bg-white shadow-sm">
                <div className="alert-header-row flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge label={alert.severity} variant={getSeverityVariant(alert.severity)} />
                    <Badge label={alert.status} variant="neutral" />
                    <span className="alert-patient-name font-bold">
                      {alert.mother_name || `Mother (${alert.mother_id.slice(0, 8)}...)`}
                    </span>
                  </div>
                  <span className="alert-timestamp text-sm text-muted">
                    Reported {formatDate(alert.created_at)}
                  </span>
                </div>

                <div className="alert-body mt-2">
                  <p className="alert-reason text-sm">
                    <strong>Trigger:</strong> {alert.trigger_reason}
                  </p>
                </div>

                <div className="alert-actions mt-3 flex flex-wrap gap-2">
                  {alert.status === 'NEW' ? (
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => handleAcknowledge(alert.id)}
                      isLoading={updatingAlertId === alert.id}
                      disabled={Boolean(updatingAlertId)}
                    >
                      Acknowledge Case
                    </Button>
                  ) : (
                    <Button variant="outline" size="sm" disabled>
                      ✓ {alert.status}
                    </Button>
                  )}
                  <Link to={`/asha/mothers/${alert.mother_id}/timeline`}>
                    <Button variant="outline" size="sm">
                      View Patient Timeline
                    </Button>
                  </Link>
                  <Link to={`/asha/mothers/${alert.mother_id}/assistant`}>
                    <Button variant="secondary" size="sm">
                      Clinical Decision Support
                    </Button>
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
};
