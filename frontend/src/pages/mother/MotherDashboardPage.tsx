import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../auth';
import { Card, Badge, Button } from '../../components/common';

export const MotherDashboardPage: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="portal-dashboard mother-dashboard" role="region" aria-labelledby="mother-dash-title">
      <header className="dashboard-header">
        <div>
          <h1 id="mother-dash-title" className="dash-title">
            Welcome, {user?.fullName || 'Mother'}
          </h1>
          <p className="dash-subtitle">
            Maternal Health Summary & Screening Overview (Phase 1 Baseline)
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
      <div className="dashboard-grid">
        <Card title="Current Screening Status" subtitle="Calculated from latest clinical readings">
          <div className="status-overview">
            <div className="status-item">
              <span className="status-label">Estimated Gestation:</span>
              <strong className="status-value">Week 24</strong>
            </div>
            <div className="status-item">
              <span className="status-label">Screening Risk Tier:</span>
              <Badge label="LOW RISK" variant="success" />
            </div>
            <div className="status-item">
              <span className="status-label">Assigned ASHA:</span>
              <strong className="status-value">Anita Devi (Community Health Worker)</strong>
            </div>
          </div>
          <div className="card-callout mt-4">
            <p className="text-muted">
              Note: Clinical risk prediction model and deterministic safety checks will integrate in Phases 4–6.
            </p>
          </div>
        </Card>

        <Card title="Recent Vital Records" subtitle="Baseline vitals tracked">
          <div className="placeholder-vitals-table">
            <p className="empty-state-notice">
              No recent vital measurements recorded yet for this session.
            </p>
            <Link to="/mother/health-entry" className="btn btn-outline btn-sm mt-3">
              Add First Vitals Entry
            </Link>
          </div>
        </Card>

        <Card title="Longitudinal Trends" subtitle="Risk trajectory over gestational weeks">
          <div className="placeholder-chart-box">
            <p className="placeholder-chart-text">
              📈 Risk Timeline Visualization will activate in Phase 4 when longitudinal health entries are linked.
            </p>
            <Link to="/mother/risk-timeline" className="text-accent underline text-sm mt-2 inline-block">
              View Risk Timeline Page →
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
};
