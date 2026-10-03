import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth';
import { healthService } from '../services/healthService';
import type { HealthStatusResponse } from '../types/api';
import { Card, Button, Badge } from '../components/common';

export const HomePage: React.FC = () => {
  const { user, isAuthenticated, login } = useAuth();
  const navigate = useNavigate();
  const [backendHealth, setBackendHealth] = useState<HealthStatusResponse | null>(null);
  const [healthLoading, setHealthLoading] = useState<boolean>(true);
  const [healthError, setHealthError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    healthService
      .checkHealth()
      .then((data) => {
        if (isMounted) {
          setBackendHealth(data);
          setHealthLoading(false);
        }
      })
      .catch((err: Error) => {
        if (isMounted) {
          setHealthError(err.message || 'Backend not currently reachable');
          setHealthLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const handleQuickLogin = async (role: 'MOTHER' | 'ASHA') => {
    await login(role);
    navigate(role === 'MOTHER' ? '/mother' : '/asha');
  };

  return (
    <div className="home-container">
      {/* Hero Section */}
      <section className="hero-section" aria-labelledby="hero-title">
        <div className="hero-content">
          <Badge label="Phase 1 Foundation" variant="info" className="mb-2" />
          <h1 id="hero-title" className="hero-title">
            Smart Maternal Health Risk Prediction & Emergency Care Coordination
          </h1>
          <p className="hero-description">
            Connecting mothers, deterministic clinical safety checks, structured ML risk screening, and ASHA community health workers in a single unified care loop.
          </p>
          
          {/* Backend Connectivity Status */}
          <div className="health-check-card" role="region" aria-label="Backend Health Status">
            <span className="health-label">FastAPI Backend Status:</span>
            {healthLoading ? (
              <span className="status-indicator status-loading">Checking connection...</span>
            ) : backendHealth ? (
              <span className="status-indicator status-online">
                🟢 Connected to {backendHealth.app} (v{backendHealth.version}, {backendHealth.environment})
              </span>
            ) : (
              <span className="status-indicator status-offline">
                ⚪ Offline / Mock Mode ({healthError})
              </span>
            )}
          </div>
        </div>
      </section>

      {/* Role Selection / Portal Navigation Section */}
      <section className="portal-selection-section" aria-labelledby="portal-select-title">
        <h2 id="portal-select-title" className="section-title">
          Select Your Care Portal
        </h2>
        <div className="portal-grid">
          {/* Mother Portal Card */}
          <Card
            title="Mother Portal"
            subtitle="Maternal health monitoring, vital entry & risk tracking"
            className="portal-card mother-card"
            footer={
              isAuthenticated && user?.role === 'MOTHER' ? (
                <Link to="/mother" className="btn btn-primary w-full">
                  Go to Mother Dashboard →
                </Link>
              ) : (
                <Button
                  variant="primary"
                  className="w-full"
                  onClick={() => handleQuickLogin('MOTHER')}
                >
                  Enter as Mother (Demo)
                </Button>
              )
            }
          >
            <ul className="portal-feature-list">
              <li>Record daily vitals and maternal symptoms</li>
              <li>View screening risk feedback & explanations</li>
              <li>Track longitudinal health history and visits</li>
              <li>Connect directly with your assigned ASHA worker</li>
            </ul>
          </Card>

          {/* ASHA Portal Card */}
          <Card
            title="ASHA Worker Portal"
            subtitle="Case triage, priority alerts & community follow-ups"
            className="portal-card asha-card"
            footer={
              isAuthenticated && user?.role === 'ASHA' ? (
                <Link to="/asha" className="btn btn-secondary w-full">
                  Go to ASHA Dashboard →
                </Link>
              ) : (
                <Button
                  variant="secondary"
                  className="w-full"
                  onClick={() => handleQuickLogin('ASHA')}
                >
                  Enter as ASHA Worker (Demo)
                </Button>
              )
            }
          >
            <ul className="portal-feature-list">
              <li>Triage high-risk and emergency escalation alerts</li>
              <li>Monitor assigned maternal cohorts across villages</li>
              <li>Log home visits, vital checks, and follow-ups</li>
              <li>Coordinate timely referrals to clinical centers</li>
            </ul>
          </Card>
        </div>
      </section>

      {/* Architecture Loop Overview */}
      <section className="architecture-overview" aria-labelledby="workflow-title">
        <h2 id="workflow-title" className="section-title">
          The MaternAI Care Coordination Workflow
        </h2>
        <div className="workflow-steps">
          <div className="workflow-step">
            <div className="step-num">1</div>
            <h4>Health Data Entry</h4>
            <p>Mother enters vitals & symptoms via web or voice</p>
          </div>
          <div className="step-arrow">→</div>
          <div className="workflow-step">
            <div className="step-num">2</div>
            <h4>Safety Engine</h4>
            <p>Deterministic checks override potential acute risks</p>
          </div>
          <div className="step-arrow">→</div>
          <div className="workflow-step">
            <div className="step-num">3</div>
            <h4>ML Risk Model</h4>
            <p>Predicts structured risk category (Low, Med, High)</p>
          </div>
          <div className="step-arrow">→</div>
          <div className="workflow-step">
            <div className="step-num">4</div>
            <h4>ASHA Coordination</h4>
            <p>Alerts route immediately to assigned health worker</p>
          </div>
        </div>
      </section>
    </div>
  );
};
