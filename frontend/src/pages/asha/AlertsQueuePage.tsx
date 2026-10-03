import React from 'react';
import { Card, Badge, Button } from '../../components/common';

export const AlertsQueuePage: React.FC = () => {
  return (
    <div className="portal-page alerts-queue-page" role="region" aria-labelledby="alerts-title">
      <header className="page-header">
        <h1 id="alerts-title" className="page-title">ASHA Escalation & Alert Queue</h1>
        <p className="page-subtitle">
          Triage and prioritize acute maternal risks triggered by safety engine thresholds or ML risk predictions.
        </p>
      </header>

      <Card title="Active Urgent Alerts" subtitle="Prioritized by clinical severity">
        <div className="alerts-list">
          <div className="alert-card-item">
            <div className="alert-header-row">
              <div className="flex items-center gap-2">
                <Badge label="HIGH PRIORITY" variant="danger" />
                <span className="alert-patient-name font-bold">Kavita Bai</span>
                <span className="text-muted text-sm">(Age 27, Gestational Week 32)</span>
              </div>
              <span className="alert-timestamp text-sm text-muted">Reported 2 hours ago</span>
            </div>

            <div className="alert-body mt-2">
              <p className="alert-reason text-sm">
                <strong>Trigger:</strong> Severe blood pressure reading (150/98 mmHg) exceeding primary safety threshold.
              </p>
              <p className="alert-recommendation text-sm text-muted">
                <strong>Required Protocol:</strong> Immediate phone contact, schedule home visit, check for pre-eclampsia symptoms.
              </p>
            </div>

            <div className="alert-actions mt-3 flex gap-2">
              <Button variant="primary" size="sm">
                Acknowledge Case
              </Button>
              <Button variant="outline" size="sm">
                Log Follow-up Visit
              </Button>
              <Button variant="secondary" size="sm">
                Call Mother (+91 9876543211)
              </Button>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};
