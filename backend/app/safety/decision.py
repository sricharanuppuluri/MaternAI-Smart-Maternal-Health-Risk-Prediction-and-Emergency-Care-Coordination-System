"""Decision Layer resolving authoritative risk and safety priority.

ARCHITECTURAL PRINCIPLE (MaternAI End-to-End Documentation Section 9):
Processing order: Validation -> Safety Rules -> ML Risk Model -> Decision Layer -> Alerts / Workflow

Documented Decision Hierarchy:
- if validation fails: VALIDATION_ERROR
- else if emergency rule: EMERGENCY
- else if concerning rule: CONCERNING
- else: use ML classification (LOW / MEDIUM / HIGH)

CRITICAL CLINICAL BOUNDARY:
The clinical mappings (e.g. EMERGENCY -> HIGH risk, EMERGENCY -> CRITICAL alert, CONCERNING -> MEDIUM risk)
are NOT explicitly defined as approved clinical rules in MaternAI PRD or End-to-End documentation.
Per docs/api_contracts.md Section 6.2, these cross-enum mappings remain explicitly deferred
pending clinical safety specification (Phase 6).
"""

from dataclasses import dataclass
from typing import Optional

from backend.app.ml.service import MLPredictionResult
from backend.app.safety.evaluator import SafetyResult
from backend.app.safety.states import SafetyStatus
from backend.app.schemas.mother import MaternalRiskLevel


def resolve_decision_state(
    validation_passed: bool,
    safety_status: SafetyStatus,
    ml_risk_level: MaternalRiskLevel,
) -> str:
    """Documented decision hierarchy resolving authoritative decision state.
    
    Source: MaternAI End-to-End Documentation Section 9.
    """
    if not validation_passed:
        return "VALIDATION_ERROR"
    if safety_status == SafetyStatus.EMERGENCY:
        return "EMERGENCY"
    if safety_status == SafetyStatus.CONCERNING:
        return "CONCERNING"
    return ml_risk_level.value


@dataclass
class DecisionResult:
    """Consolidated clinical decision resolving safety precedence."""
    decision_state: str  # Authoritative decision hierarchy state (EMERGENCY, CONCERNING, LOW, MEDIUM, HIGH)
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
        """Resolve authoritative decision state enforcing safety precedence.
        
        The authoritative hierarchy state (decision_state) strictly prioritizes deterministic safety.
        The categorical ML risk_level is preserved from the model provider, avoiding inventing
        an unapproved clinical conversion rule between SafetyStatus and MaternalRiskLevel.
        """
        # Resolve authoritative hierarchy state per MaternAI documentation
        dec_state = resolve_decision_state(
            validation_passed=True,
            safety_status=safety_result.status,
            ml_risk_level=prediction_result.risk_level,
        )

        trigger_reason: Optional[str] = None
        action_required: Optional[str] = None

        if safety_result.status == SafetyStatus.EMERGENCY:
            trigger_reason = ", ".join(safety_result.triggered_rules) or "Deterministic emergency safety rule triggered"
            action_required = safety_result.action_required or "Immediate clinical emergency response required"
        elif safety_result.status == SafetyStatus.CONCERNING:
            trigger_reason = ", ".join(safety_result.triggered_rules) or "Deterministic concerning condition detected"
            action_required = safety_result.action_required or "Prompt ASHA worker follow-up recommended"

        return DecisionResult(
            decision_state=dec_state,
            final_risk_level=prediction_result.risk_level,
            safety_status=safety_result.status,
            model_score=prediction_result.model_score,
            model_version=prediction_result.model_version,
            feature_schema_version=prediction_result.feature_schema_version,
            trigger_reason=trigger_reason,
            action_required=action_required,
        )



# Global decision engine instance
decision_engine = DecisionEngine()


def get_decision_engine() -> DecisionEngine:
    """Dependency provider for decision engine."""
    return decision_engine
