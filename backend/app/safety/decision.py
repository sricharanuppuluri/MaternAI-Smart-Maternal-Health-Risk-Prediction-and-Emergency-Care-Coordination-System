"""Decision Layer resolving authoritative risk and safety priority.

CRITICAL ARCHITECTURAL INVARIANT:
Deterministic safety rules ALWAYS override Machine Learning risk classifications.
- EMERGENCY safety status forces final risk level to HIGH. ML prediction CANNOT downgrade it.
- CONCERNING safety status forces final risk level to at least MEDIUM.
- CLEAR safety status defers to the ML screening classification.
"""

from dataclasses import dataclass
from typing import Optional

from backend.app.ml.service import MLPredictionResult
from backend.app.safety.evaluator import SafetyResult
from backend.app.safety.states import SafetyStatus
from backend.app.schemas.mother import MaternalRiskLevel


@dataclass
class DecisionResult:
    """Consolidated clinical decision resolving safety precedence."""
    final_risk_level: MaternalRiskLevel
    safety_status: SafetyStatus
    model_score: Optional[float]
    model_version: str
    feature_schema_version: str
    trigger_reason: Optional[str]
    action_required: Optional[str]


class DecisionEngine:
    """Engine synthesizing safety rules and ML predictions into authoritative decision state."""

    @staticmethod
    def resolve(
        safety_result: SafetyResult,
        prediction_result: MLPredictionResult,
    ) -> DecisionResult:
        """Resolve authoritative risk level enforcing safety precedence."""
        # 1. Deterministic EMERGENCY overrides all ML outputs
        if safety_result.status == SafetyStatus.EMERGENCY:
            return DecisionResult(
                final_risk_level=MaternalRiskLevel.HIGH,
                safety_status=SafetyStatus.EMERGENCY,
                model_score=prediction_result.model_score,
                model_version=prediction_result.model_version,
                feature_schema_version=prediction_result.feature_schema_version,
                trigger_reason=", ".join(safety_result.triggered_rules) or "Deterministic emergency safety rule triggered",
                action_required=safety_result.action_required or "Immediate clinical emergency response required",
            )

        # 2. Deterministic CONCERNING elevates risk to at least MEDIUM
        if safety_result.status == SafetyStatus.CONCERNING:
            elevated_risk = (
                MaternalRiskLevel.HIGH
                if prediction_result.risk_level == MaternalRiskLevel.HIGH
                else MaternalRiskLevel.MEDIUM
            )
            return DecisionResult(
                final_risk_level=elevated_risk,
                safety_status=SafetyStatus.CONCERNING,
                model_score=prediction_result.model_score,
                model_version=prediction_result.model_version,
                feature_schema_version=prediction_result.feature_schema_version,
                trigger_reason=", ".join(safety_result.triggered_rules) or "Deterministic concerning condition detected",
                action_required=safety_result.action_required or "Prompt ASHA worker follow-up recommended",
            )

        # 3. Deterministic CLEAR defers to ML model prediction
        return DecisionResult(
            final_risk_level=prediction_result.risk_level,
            safety_status=SafetyStatus.CLEAR,
            model_score=prediction_result.model_score,
            model_version=prediction_result.model_version,
            feature_schema_version=prediction_result.feature_schema_version,
            trigger_reason=None,
            action_required=None,
        )


# Global decision engine instance
decision_engine = DecisionEngine()


def get_decision_engine() -> DecisionEngine:
    """Dependency provider for decision engine."""
    return decision_engine
