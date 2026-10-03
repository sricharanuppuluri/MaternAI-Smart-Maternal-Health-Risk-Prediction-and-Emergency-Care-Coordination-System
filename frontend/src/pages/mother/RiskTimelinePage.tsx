import React from 'react';
import { Card, Badge } from '../../components/common';

export const RiskTimelinePage: React.FC = () => {
  return (
    <div className="portal-page risk-timeline-page" role="region" aria-labelledby="timeline-title">
      <header className="page-header">
        <h1 id="timeline-title" className="page-title">Longitudinal Risk Timeline</h1>
        <p className="page-subtitle">
          Historical overview of clinical measurements, safety events, and ML risk evaluations.
        </p>
      </header>

      <Card title="Gestation Journey" subtitle="Trajectory across pregnancy milestones">
        <div className="timeline-placeholder-list">
          <div className="timeline-entry">
            <div className="timeline-marker marker-active" />
            <div className="timeline-info">
              <div className="timeline-date-row">
                <span className="timeline-week font-bold">Week 24 (Current)</span>
                <Badge label="LOW RISK" variant="success" />
              </div>
              <p className="timeline-notes text-sm text-muted">
                Blood pressure 118/76 mmHg. No high-risk red-flag symptoms reported.
              </p>
            </div>
          </div>

          <div className="timeline-entry">
            <div className="timeline-marker" />
            <div className="timeline-info">
              <div className="timeline-date-row">
                <span className="timeline-week font-bold">Week 20 Checkpoint</span>
                <Badge label="LOW RISK" variant="success" />
              </div>
              <p className="timeline-notes text-sm text-muted">
                Routine ASHA screening visit recorded. Vitals normal.
              </p>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};
