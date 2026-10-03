/**
 * Risk Assessment Result presentation component.
 *
 * Displays:
 * - Categorical risk tier: LOW, MEDIUM, HIGH (authoritative backend output)
 * - Explainability breakdown: contributing factors (INCREASES_RISK vs DECREASES_RISK) with values
 * - Clinical decision-support disclaimer (not a medical diagnosis)
 *
 * Safety Rules:
 * - Never converts model_score into a probability percentage or medical diagnosis
 * - Does not invent clinical rules or calculate risk in frontend
 */

import React from 'react';
import type { PredictionResponse, MaternalRiskLevel, ContributingFactor } from '../../types/mother';
import type { ApiErrorDetail } from '../../types/api';
import { Card, Badge, AlertBanner, Button } from '../common';
import { formatDate } from '../../utils/formatters';

export interface RiskAssessmentCardProps {
  prediction: PredictionResponse | null;
  isLoading?: boolean;
  error?: ApiErrorDetail | string | null;
  onRetry?: () => void;
  className?: string;
}

export const RiskAssessmentCard: React.FC<RiskAssessmentCardProps> = ({
  prediction,
  isLoading = false,
  error = null,
  onRetry,
  className = '',
}) => {
  if (isLoading) {
    return (
      <Card
        title="Risk Assessment Screening"
        subtitle="Evaluating measurements against decision-support models"
        className={className}
      >
        <div className="risk-loading-state p-4 text-center" role="status" aria-live="polite">
          <div className="spinner mx-auto mb-2" />
          <p className="text-muted">Evaluating clinical measurements against ML decision-support model...</p>
        </div>
      </Card>
    );
  }

  if (error) {
    const errorMsg = typeof error === 'string' ? error : error.message || 'Unable to complete risk evaluation.';
    return (
      <Card title="Risk Assessment Screening" className={className}>
        <AlertBanner type="danger" message={errorMsg} />
        {onRetry && (
          <div className="mt-3">
            <Button variant="outline" size="sm" onClick={onRetry}>
              Retry Screening Evaluation
            </Button>
          </div>
        )}
      </Card>
    );
  }

  if (!prediction) {
    return (
      <Card title="Risk Assessment Screening" className={className}>
        <div className="risk-empty-state p-4 text-center">
          <p className="text-muted">No risk assessment available yet.</p>
        </div>
      </Card>
    );
  }

  const getRiskBadgeVariant = (level: MaternalRiskLevel): 'success' | 'warning' | 'danger' => {
    switch (level) {
      case 'HIGH':
        return 'danger';
      case 'MEDIUM':
        return 'warning';
      case 'LOW':
      default:
        return 'success';
    }
  };

  const getFactorBadgeVariant = (direction: string): 'danger' | 'success' | 'neutral' => {
    if (direction === 'INCREASES_RISK') return 'danger';
    if (direction === 'DECREASES_RISK') return 'success';
    return 'neutral';
  };

  const formatFeatureName = (feature: string): string => {
    return feature
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (char) => char.toUpperCase());
  };

  return (
    <Card
      title="Maternal Risk Screening Result"
      subtitle={`Evaluated via Model ${prediction.model_version}`}
      className={`risk-assessment-card ${className}`}
    >
      {/* Tier Outcome Display */}
      <div className="risk-tier-outcome p-3 rounded mb-3 flex items-center justify-between">
        <div>
          <span className="text-xs font-semibold text-muted uppercase tracking-wider block mb-1">
            Authoritative Screening Tier
          </span>
          <div className="flex items-center gap-2">
            <Badge
              label={`${prediction.risk_level} RISK`}
              variant={getRiskBadgeVariant(prediction.risk_level)}
              className="risk-tier-badge text-sm font-bold"
            />
            <span className="text-sm font-medium text-muted">
              {`${prediction.risk_level} RISK — Screening result`}
            </span>
          </div>
        </div>
        <div className="text-right text-xs text-muted">
          <span>Screened: {formatDate(prediction.created_at)}</span>
        </div>
      </div>

      {/* Mandatory Decision-Support Notice */}
      <div className="clinical-advisory-notice p-3 bg-neutral-light border rounded mb-3 text-xs text-muted">
        <strong>Clinical Decision-Support Notice:</strong> This assessment is an automated screening aid
        generated from vital signs and reported symptoms. It is <em>not</em> an autonomous diagnostic determination
        or treatment prescription. Certified healthcare providers and ASHA health workers remain authoritative for
        all maternal clinical care decisions.
      </div>

      {/* Contributing Explainability Factors */}
      {prediction.contributing_factors && prediction.contributing_factors.length > 0 && (
        <div className="contributing-factors-section mt-4">
          <h4 className="text-sm font-semibold mb-2">Key Contributing Factors & Clinical Indicators:</h4>
          <ul className="factors-list space-y-2 list-none p-0 m-0">
            {prediction.contributing_factors.map((factor: ContributingFactor, idx: number) => (
              <li
                key={`${factor.feature}-${idx}`}
                className="factor-item flex items-center justify-between p-2 border rounded bg-white text-sm"
              >
                <div className="flex items-center gap-2">
                  <span className="factor-name font-medium">{formatFeatureName(factor.feature)}</span>
                  {factor.value !== undefined && factor.value !== null && (
                    <span className="factor-value text-xs text-muted">
                      (Observed: {String(factor.value)})
                    </span>
                  )}
                </div>
                <Badge
                  label={factor.direction === 'INCREASES_RISK' ? 'Increases Risk' : 'Decreases Risk'}
                  variant={getFactorBadgeVariant(factor.direction)}
                  className="factor-direction text-xs"
                />
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Model Version Meta */}
      <div className="model-meta mt-3 pt-2 border-t text-xs text-muted flex justify-between">
        <span>Model Version: {prediction.model_version}</span>
        <span>Schema Version: {prediction.feature_schema_version}</span>
      </div>
    </Card>
  );
};
