import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, Input, Button, AlertBanner } from '../../components/common';
import { RiskAssessmentCard } from '../../components/clinical/RiskAssessmentCard';
import { healthRecordService, symptomService, predictionService } from '../../services';
import type { HealthRecordCreate, PredictionResponse, SymptomItem } from '../../types/mother';

const COMMON_SYMPTOMS = [
  { code: 'headache', label: 'Severe / Persistent Headache' },
  { code: 'swelling_feet', label: 'Swelling in Feet or Ankles' },
  { code: 'dizziness', label: 'Dizziness or Lightheadedness' },
  { code: 'blurred_vision', label: 'Visual Disturbances / Blurred Vision' },
  { code: 'abdominal_pain', label: 'Abdominal or Epigastric Pain' },
];

export const HealthRecordEntryPage: React.FC = () => {
  // Clinical measurement form state
  const [pregnancyWeek, setPregnancyWeek] = useState('26');
  const [systolic, setSystolic] = useState('120');
  const [diastolic, setDiastolic] = useState('80');
  const [glucose, setGlucose] = useState('95');
  const [hemoglobin, setHemoglobin] = useState('11.5');
  const [weightKg, setWeightKg] = useState('62.5');
  const [bodyTemp, setBodyTemp] = useState('36.8');
  const [heartRate, setHeartRate] = useState('76');

  // Symptoms state
  const [selectedSymptomCodes, setSelectedSymptomCodes] = useState<string[]>([]);
  const [symptomNotes, setSymptomNotes] = useState('');

  // Flow and outcome states
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [predictionResult, setPredictionResult] = useState<PredictionResponse | null>(null);

  const toggleSymptom = (code: string) => {
    setSelectedSymptomCodes((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setSubmitError(null);

    try {
      // 1. Submit Health Record (POST /api/v1/health-records)
      const hrPayload: HealthRecordCreate = {
        pregnancy_week: pregnancyWeek ? parseInt(pregnancyWeek, 10) : undefined,
        systolic_bp: systolic ? parseFloat(systolic) : undefined,
        diastolic_bp: diastolic ? parseFloat(diastolic) : undefined,
        blood_sugar: glucose ? parseFloat(glucose) : undefined,
        hemoglobin: hemoglobin ? parseFloat(hemoglobin) : undefined,
        weight_kg: weightKg ? parseFloat(weightKg) : undefined,
        body_temperature: bodyTemp ? parseFloat(bodyTemp) : undefined,
        heart_rate: heartRate ? parseFloat(heartRate) : undefined,
        recorded_at: new Date().toISOString(),
      };

      const hrResponse = await healthRecordService.createHealthRecord(hrPayload);
      const healthRecordId = hrResponse.id;

      // 2. Submit Symptoms if any were reported (POST /api/v1/symptoms)
      if (selectedSymptomCodes.length > 0 && healthRecordId) {
        const symptomsList: SymptomItem[] = selectedSymptomCodes.map((code) => ({
          symptom_code: code,
          severity: 2,
          notes: symptomNotes || undefined,
        }));

        await symptomService.recordSymptoms({
          health_record_id: healthRecordId,
          symptoms: symptomsList,
        });
      }

      // 3. Trigger ML Risk Prediction (POST /api/v1/predictions)
      const predResponse = await predictionService.requestPrediction({
        health_record_id: healthRecordId,
      });

      setPredictionResult(predResponse);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to complete maternal health screening flow.';
      setSubmitError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReset = () => {
    setPredictionResult(null);
    setSubmitError(null);
    setSelectedSymptomCodes([]);
    setSymptomNotes('');
  };

  return (
    <div className="portal-page health-entry-page" role="region" aria-labelledby="health-entry-title">
      <header className="page-header mb-4">
        <h1 id="health-entry-title" className="page-title text-2xl font-bold">
          Maternal Health Data Entry & Risk Screening
        </h1>
        <p className="page-subtitle text-muted text-sm">
          Record vital physical measurements and current symptoms to trigger automated clinical risk evaluation.
        </p>
      </header>

      {submitError && (
        <AlertBanner
          type="danger"
          message={submitError}
          onDismiss={() => setSubmitError(null)}
        />
      )}

      {/* Outcome: Render Risk Assessment Result when available */}
      {predictionResult ? (
        <div className="prediction-outcome-view space-y-4">
          <RiskAssessmentCard prediction={predictionResult} />
          <div className="flex gap-3">
            <Button variant="primary" onClick={handleReset}>
              + Record Another Checkup
            </Button>
            <Link to="/mother/risk-timeline" className="btn btn-outline">
              View on Risk Timeline →
            </Link>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="vitals-form space-y-4" noValidate>
          <Card title="1. Vital Signs & Clinical Measurements" subtitle="Latest observations">
            <div className="form-grid grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Input
                id="pregnancy-week"
                label="Gestational Week"
                type="number"
                placeholder="e.g. 26"
                value={pregnancyWeek}
                onChange={(e) => setPregnancyWeek(e.target.value)}
                helperText="1–45 weeks"
                required
              />

              <Input
                id="systolic-bp"
                label="Systolic BP (mmHg)"
                type="number"
                placeholder="e.g. 120"
                value={systolic}
                onChange={(e) => setSystolic(e.target.value)}
                helperText="Target: 90–120 mmHg"
                required
              />

              <Input
                id="diastolic-bp"
                label="Diastolic BP (mmHg)"
                type="number"
                placeholder="e.g. 80"
                value={diastolic}
                onChange={(e) => setDiastolic(e.target.value)}
                helperText="Target: 60–80 mmHg"
                required
              />

              <Input
                id="blood-sugar"
                label="Blood Sugar (mg/dL)"
                type="number"
                placeholder="e.g. 95"
                value={glucose}
                onChange={(e) => setGlucose(e.target.value)}
                helperText="Fasting / random glucose"
              />

              <Input
                id="hemoglobin"
                label="Hemoglobin (g/dL)"
                type="number"
                placeholder="e.g. 11.5"
                value={hemoglobin}
                onChange={(e) => setHemoglobin(e.target.value)}
                helperText="Target: ≥ 11.0 g/dL"
              />

              <Input
                id="weight-kg"
                label="Weight (kg)"
                type="number"
                placeholder="e.g. 62.5"
                value={weightKg}
                onChange={(e) => setWeightKg(e.target.value)}
                helperText="Current maternal weight"
              />

              <Input
                id="body-temp"
                label="Body Temp (°C)"
                type="number"
                placeholder="e.g. 36.8"
                value={bodyTemp}
                onChange={(e) => setBodyTemp(e.target.value)}
                helperText="Oral / axillary"
              />

              <Input
                id="heart-rate"
                label="Heart Rate (bpm)"
                type="number"
                placeholder="e.g. 76"
                value={heartRate}
                onChange={(e) => setHeartRate(e.target.value)}
                helperText="Resting pulse"
              />
            </div>
          </Card>

          <Card title="2. Reported Maternal Symptoms" subtitle="Check any active symptoms">
            <div className="symptoms-checkbox-grid grid grid-cols-1 md:grid-cols-2 gap-2 mb-3">
              {COMMON_SYMPTOMS.map((sym) => {
                const isChecked = selectedSymptomCodes.includes(sym.code);
                return (
                  <label
                    key={sym.code}
                    className={`symptom-checkbox-label flex items-center gap-2 p-2 border rounded cursor-pointer ${
                      isChecked ? 'bg-primary-light border-primary' : 'bg-white'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={() => toggleSymptom(sym.code)}
                      className="cursor-pointer"
                    />
                    <span className="text-sm">{sym.label}</span>
                  </label>
                );
              })}
            </div>

            <Input
              id="symptom-notes"
              label="Additional Notes / Clinical Observations"
              type="text"
              placeholder="e.g. Mild headache began this morning after walking"
              value={symptomNotes}
              onChange={(e) => setSymptomNotes(e.target.value)}
            />
          </Card>

          <div className="form-actions mt-4 flex items-center gap-3">
            <Button
              type="submit"
              variant="primary"
              isLoading={isSubmitting}
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Evaluating Clinical Risk...' : 'Submit Health Check & Evaluate Risk'}
            </Button>
          </div>
        </form>
      )}
    </div>
  );
};
