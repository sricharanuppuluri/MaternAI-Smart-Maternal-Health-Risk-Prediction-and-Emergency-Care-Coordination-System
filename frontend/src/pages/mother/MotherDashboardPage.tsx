import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../auth';
import { Card, Badge, Button } from '../../components/common';
import { timelineService } from '../../services';
import type { RiskTimelineResponse, MaternalRiskLevel } from '../../types/mother';
import { formatDate } from '../../utils/formatters';

export const MotherDashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [timeline, setTimeline] = useState<RiskTimelineResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    let isMounted = true;

    async function loadRiskStatus() {
      if (!user?.id) {
        setIsLoading(false);
        return;
      }

      try {
        const data = await timelineService.getRiskTimeline(user.id);
        if (isMounted) {
          setTimeline(data);
        }
      } catch {
        // Timeline may not be populated yet for new accounts; handled as no-assessment state
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadRiskStatus();

    return () => {
      isMounted = false;
    };
  }, [user?.id]);

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

  const currentRisk = timeline?.current_risk_level;
  const latestAssessment = timeline?.assessments && timeline.assessments.length > 0 ? timeline.assessments[0] : null;

  return (
    <div className="portal-dashboard mother-dashboard" role="region" aria-labelledby="mother-dash-title">
      <header className="dashboard-header mb-4 flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div>
          <h1 id="mother-dash-title" className="dash-title text-2xl font-bold">
            Welcome, {user?.fullName || user?.full_name || 'Mother'}
          </h1>
          <p className="dash-subtitle text-muted text-sm">
            Maternal Health Summary & Clinical Risk Screening Portal
          </p>
        </div>
        <div className="header-actions">
          <Link to="/mother/health-entry">
            <Button variant="primary">
              + Record Health Check
            </Button>
          </Link>
        </div>
      </header>

      {/* Status & Alerts Grid */}
      <div className="dashboard-grid grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Card 1: Authoritative Screening Status */}
        <Card title="Current Screening Status" subtitle="Decision-support evaluation">
          <div className="status-overview space-y-3">
            <div className="status-item flex items-center justify-between">
              <span className="status-label text-sm text-muted">Authoritative Risk Tier:</span>
              {isLoading ? (
                <span className="text-xs text-muted">Checking status...</span>
              ) : currentRisk ? (
                <Badge label={`${currentRisk} RISK`} variant={getRiskBadgeVariant(currentRisk)} />
              ) : (
                <Badge label="NO ASSESSMENT" variant="neutral" />
              )}
            </div>

            <div className="status-item flex items-center justify-between">
              <span className="status-label text-sm text-muted">Status Notice:</span>
              <span className="status-value text-xs font-medium text-muted">
                {currentRisk ? (
                  currentRisk === 'HIGH' ? 'Requires urgent medical / ASHA consultation' :
                  currentRisk === 'MEDIUM' ? 'Requires routine ASHA monitoring' :
                  'Normal baseline monitoring'
                ) : (
                  'No risk assessment available yet.'
                )}
              </span>
            </div>

            <div className="status-item flex items-center justify-between">
              <span className="status-label text-sm text-muted">Assigned Caregiver:</span>
              <strong className="status-value text-xs">Anita Devi (ASHA Health Worker)</strong>
            </div>
          </div>

          <div className="card-callout mt-4 p-2 bg-neutral-light border rounded text-xs text-muted">
            <p>
              Note: Clinical assessments provide automated decision support and triage assistance. Certified healthcare providers remain authoritative.
            </p>
          </div>
        </Card>

        {/* Card 2: Latest Vitals & Assessment Summary */}
        <Card title="Latest Clinical Readings" subtitle="Most recent recorded vitals">
          {latestAssessment ? (
            <div className="vitals-summary space-y-2 text-sm">
              <div className="flex justify-between border-b pb-1">
                <span className="text-muted">Assessment Type:</span>
                <strong>{latestAssessment.assessment_type}</strong>
              </div>
              {latestAssessment.systolic_bp && latestAssessment.diastolic_bp && (
                <div className="flex justify-between border-b pb-1">
                  <span className="text-muted">Blood Pressure:</span>
                  <strong>{latestAssessment.systolic_bp} / {latestAssessment.diastolic_bp} mmHg</strong>
                </div>
              )}
              {latestAssessment.blood_sugar && (
                <div className="flex justify-between border-b pb-1">
                  <span className="text-muted">Blood Glucose:</span>
                  <strong>{latestAssessment.blood_sugar} mg/dL</strong>
                </div>
              )}
              {latestAssessment.hemoglobin && (
                <div className="flex justify-between border-b pb-1">
                  <span className="text-muted">Hemoglobin:</span>
                  <strong>{latestAssessment.hemoglobin} g/dL</strong>
                </div>
              )}
              <div className="flex justify-between text-xs text-muted pt-1">
                <span>Recorded:</span>
                <span>{formatDate(latestAssessment.timestamp)}</span>
              </div>
            </div>
          ) : (
            <div className="placeholder-vitals-table text-center p-4">
              <p className="empty-state-notice text-sm text-muted mb-3">
                No risk assessment available yet.
              </p>
              <Link to="/mother/health-entry" className="btn btn-outline btn-sm">
                Add First Health Entry
              </Link>
            </div>
          )}
        </Card>

        {/* Card 3: Longitudinal Risk Trajectory */}
        <Card title="Longitudinal Trends" subtitle="Trajectory across gestational milestones">
          <div className="trends-box space-y-3">
            <p className="text-sm text-muted">
              {timeline?.assessments && timeline.assessments.length > 0
                ? `${timeline.assessments.length} clinical assessment(s) recorded along pregnancy journey.`
                : 'Longitudinal risk trajectory activates as clinical recordings are added.'}
            </p>
            <div>
              <Link to="/mother/risk-timeline" className="text-accent underline text-sm inline-block">
                View Full Risk Timeline →
              </Link>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};
