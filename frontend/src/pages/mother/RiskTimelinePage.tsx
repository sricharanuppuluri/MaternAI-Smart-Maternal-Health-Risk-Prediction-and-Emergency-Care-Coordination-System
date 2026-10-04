import React, { useEffect, useState, useCallback } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Card, Badge, AlertBanner, Button } from '../../components/common';
import { useAuth } from '../../auth';
import { timelineService } from '../../services';
import type { RiskTimelineResponse, MaternalRiskLevel, RiskTimelinePoint } from '../../types/mother';
import { formatDate } from '../../utils/formatters';

export const RiskTimelinePage: React.FC = () => {
  const { user } = useAuth();
  const { motherId: routeMotherId } = useParams<{ motherId?: string }>();
  const targetMotherId = routeMotherId || user?.id;
  const isAshaView = Boolean(routeMotherId && routeMotherId !== user?.id);

  const [timeline, setTimeline] = useState<RiskTimelineResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(() => Boolean(targetMotherId));
  const [error, setError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState<number>(0);

  useEffect(() => {
    let isMounted = true;

    if (!targetMotherId) {
      return;
    }

    timelineService
      .getRiskTimeline(targetMotherId)
      .then((data) => {
        if (isMounted) {
          setTimeline(data);
          setError(null);
        }
      })
      .catch((err: unknown) => {
        if (isMounted) {
          const msg = err instanceof Error ? err.message : 'Unable to load longitudinal risk timeline.';
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
  }, [targetMotherId, refreshKey]);

  const handleRefresh = useCallback(() => {
    setIsLoading(true);
    setError(null);
    setRefreshKey((prev) => prev + 1);
  }, []);

  const getRiskBadgeVariant = (level?: MaternalRiskLevel | null): 'success' | 'warning' | 'danger' | 'neutral' => {
    switch (level) {
      case 'HIGH':
        return 'danger';
      case 'MEDIUM':
        return 'warning';
      case 'LOW':
        return 'success';
      default:
        return 'neutral';
    }
  };

  return (
    <div className="portal-page risk-timeline-page" role="region" aria-labelledby="timeline-title">
      {isAshaView && (
        <div className="mb-2">
          <Link to="/asha/mothers" className="text-sm text-primary underline">
            &larr; Back to Assigned Mothers
          </Link>
        </div>
      )}
      <header className="page-header mb-4 flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div>
          <h1 id="timeline-title" className="page-title text-2xl font-bold">
            Longitudinal Maternal Risk Timeline{isAshaView ? ` (Mother ID: ${targetMotherId})` : ''}
          </h1>
          <p className="page-subtitle text-muted text-sm">
            Chronological record of vital trends, screening risk tiers, and clinical safety events.
          </p>
        </div>
        {!isAshaView && (
          <div className="header-actions">
            <Link to="/mother/health-entry" className="btn btn-primary btn-sm">
              + Record New Vitals
            </Link>
          </div>
        )}
      </header>

      {/* Loading State */}
      {isLoading && (
        <Card title="Gestation Journey">
          <div className="p-6 text-center" role="status" aria-live="polite">
            <div className="spinner mx-auto mb-2" />
            <p className="text-muted">Loading longitudinal risk history...</p>
          </div>
        </Card>
      )}

      {/* Error State */}
      {!isLoading && error && (
        <div className="space-y-3">
          <AlertBanner type="danger" message={error} />
          <Button variant="outline" size="sm" onClick={handleRefresh}>
            Retry Loading Timeline
          </Button>
        </div>
      )}

      {/* Populated / Empty States */}
      {!isLoading && !error && (
        <div className="space-y-4">
          {/* Current Risk Level Header Card */}
          <Card title="Current Trajectory Status">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-2">
              <div>
                <span className="text-xs text-muted uppercase font-semibold block mb-1">
                  Authoritative Current Tier
                </span>
                <div className="flex items-center gap-2">
                  <Badge
                    label={timeline?.current_risk_level ? `${timeline.current_risk_level} RISK` : 'NO ASSESSMENT'}
                    variant={getRiskBadgeVariant(timeline?.current_risk_level)}
                    className="text-sm font-bold"
                  />
                  <span className="text-sm text-muted">
                    {timeline?.current_risk_level
                      ? `${timeline.current_risk_level} RISK — Screening result`
                      : 'No baseline risk screening completed yet'}
                  </span>
                </div>
              </div>
              <div className="text-xs text-muted">
                <span>Total Historical Screenings: {timeline?.assessments?.length || 0}</span>
              </div>
            </div>
          </Card>

          {/* Timeline Assessments List */}
          <Card title="Chronological Assessments" subtitle="Longitudinal maternal assessments">
            {(!timeline?.assessments || timeline.assessments.length === 0) ? (
              <div className="empty-timeline-state p-6 text-center text-muted">
                <p className="mb-3">No historical risk assessments recorded yet for this patient profile.</p>
                <Link to="/mother/health-entry" className="btn btn-outline btn-sm">
                  Record First Health Entry →
                </Link>
              </div>
            ) : (
              <div className="timeline-list space-y-4">
                {timeline.assessments.map((item: RiskTimelinePoint, index: number) => (
                  <div
                    key={`${item.timestamp}-${index}`}
                    className="timeline-item p-3 border rounded bg-white shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-3"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Badge
                          label={`${item.risk_level} RISK`}
                          variant={getRiskBadgeVariant(item.risk_level)}
                          className="text-xs"
                        />
                        <span className="text-xs uppercase tracking-wider font-semibold text-muted">
                          [{item.assessment_type}]
                        </span>
                        <span className="text-xs text-muted">
                          {formatDate(item.timestamp)}
                        </span>
                      </div>

                      {item.trigger_reason && (
                        <p className="text-sm text-danger font-medium mt-1">
                          Trigger: {item.trigger_reason}
                        </p>
                      )}

                      {/* Associated Vitals Summary */}
                      <div className="vitals-snippet text-xs text-muted flex flex-wrap gap-x-4 gap-y-1 mt-1">
                        {item.systolic_bp !== undefined && item.systolic_bp !== null && item.diastolic_bp !== undefined && item.diastolic_bp !== null && (
                          <span>BP: <strong>{item.systolic_bp}/{item.diastolic_bp} mmHg</strong></span>
                        )}
                        {item.hemoglobin !== undefined && item.hemoglobin !== null && (
                          <span>Hb: <strong>{item.hemoglobin} g/dL</strong></span>
                        )}
                        {item.blood_sugar !== undefined && item.blood_sugar !== null && (
                          <span>Glucose: <strong>{item.blood_sugar} mg/dL</strong></span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  );
};
