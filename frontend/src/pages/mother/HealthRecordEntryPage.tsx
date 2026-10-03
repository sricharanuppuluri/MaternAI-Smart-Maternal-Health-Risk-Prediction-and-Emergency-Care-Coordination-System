import React, { useState } from 'react';
import { Card, Input, Button, AlertBanner } from '../../components/common';

export const HealthRecordEntryPage: React.FC = () => {
  const [systolic, setSystolic] = useState('');
  const [diastolic, setDiastolic] = useState('');
  const [glucose, setGlucose] = useState('');
  const [heartRate, setHeartRate] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Phase 1 UI confirmation placeholder (Phase 4 connects to POST /api/v1/health-records)
    setSubmitted(true);
  };

  return (
    <div className="portal-page health-entry-page" role="region" aria-labelledby="health-entry-title">
      <header className="page-header">
        <h1 id="health-entry-title" className="page-title">Maternal Health Data Entry</h1>
        <p className="page-subtitle">
          Record vital measurements and maternal symptoms for screening risk assessment.
        </p>
      </header>

      {submitted && (
        <AlertBanner
          type="success"
          title="Phase 1 Foundation Verification"
          message="Health measurement form inputs validated. Real-time submission will connect to FastAPI POST /api/v1/health-records in Phase 4."
          onDismiss={() => setSubmitted(false)}
        />
      )}

      <Card title="Clinical Measurements" subtitle="Enter your latest physical checkup parameters">
        <form onSubmit={handleSubmit} className="vitals-form">
          <div className="form-grid">
            <Input
              id="systolic-bp"
              label="Systolic Blood Pressure (mmHg)"
              type="number"
              placeholder="e.g. 120"
              value={systolic}
              onChange={(e) => setSystolic(e.target.value)}
              helperText="Normal target: 90–120 mmHg"
            />

            <Input
              id="diastolic-bp"
              label="Diastolic Blood Pressure (mmHg)"
              type="number"
              placeholder="e.g. 80"
              value={diastolic}
              onChange={(e) => setDiastolic(e.target.value)}
              helperText="Normal target: 60–80 mmHg"
            />

            <Input
              id="blood-glucose"
              label="Blood Glucose (mg/dL)"
              type="number"
              placeholder="e.g. 95"
              value={glucose}
              onChange={(e) => setGlucose(e.target.value)}
              helperText="Fasting or random reading"
            />

            <Input
              id="heart-rate"
              label="Heart Rate (bpm)"
              type="number"
              placeholder="e.g. 75"
              value={heartRate}
              onChange={(e) => setHeartRate(e.target.value)}
              helperText="Resting pulse"
            />
          </div>

          <div className="form-actions mt-4">
            <Button type="submit" variant="primary">
              Validate & Preview Measurements (Demo)
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
};
