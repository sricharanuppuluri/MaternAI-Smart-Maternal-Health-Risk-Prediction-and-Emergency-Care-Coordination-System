import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../auth';
import { Card, Badge, Button } from '../../components/common';

export const AshaDashboardPage: React.FC = () => {
  const { user } = useAuth();

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
              ⚠️ Review Alerts (1 Active)
            </Button>
          </Link>
        </div>
      </header>

      {/* Case Metrics Grid */}
      <div className="metrics-grid">
        <div className="metric-card">
          <span className="metric-label">Assigned Mothers</span>
          <strong className="metric-value">28</strong>
        </div>
        <div className="metric-card alert-metric">
          <span className="metric-label">Pending Escalation Alerts</span>
          <strong className="metric-value text-danger">1</strong>
        </div>
        <div className="metric-card">
          <span className="metric-label">Scheduled Home Visits</span>
          <strong className="metric-value">4</strong>
        </div>
        <div className="metric-card">
          <span className="metric-label">Resolved This Month</span>
          <strong className="metric-value text-success">12</strong>
        </div>
      </div>

      <div className="dashboard-grid mt-4">
        <Card title="High Priority Alerts" subtitle="Cases flagged by deterministic safety rules or high-risk ML predictions">
          <div className="alert-item-row">
            <div>
              <div className="flex items-center gap-2">
                <Badge label="HIGH RISK" variant="danger" />
                <strong>Kavita Bai (Week 32)</strong>
              </div>
              <p className="text-sm text-muted mt-1">
                Elevated blood pressure (150/98 mmHg) flagged during self-check. Requires prompt follow-up visit.
              </p>
            </div>
            <Link to="/asha/alerts" className="btn btn-outline btn-sm">
              Triage Alert →
            </Link>
          </div>
        </Card>

        <Card title="Assigned Mothers Roster" subtitle="Maternal cohort under care">
          <p className="text-sm text-muted">
            Directly monitor vital recordings, overdue checkups, and delivery planning.
          </p>
          <div className="mt-3">
            <Link to="/asha/mothers" className="btn btn-secondary btn-sm">
              View All 28 Mothers →
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
};
