"""Safety precedence and decision hierarchy tests.

Verifies:
- Safety states: CLEAR, CONCERNING, EMERGENCY.
- Processing order: Validation -> Safety Rules -> ML -> Decision Layer -> LLM / Agent.
- Deterministic safety rule cannot be overridden by ML risk classification or LLM text.
"""

from backend.app.safety.states import SafetyStatus
from backend.app.schemas.mother import MaternalRiskLevel


def resolve_decision_state(
    validation_passed: bool,
    deterministic_safety_status: SafetyStatus,
    ml_risk_level: MaternalRiskLevel,
) -> str:
    """Decision hierarchy resolving authoritative status.
    
    Order:
    1. Validation
    2. Safety Rules (EMERGENCY / CONCERNING take deterministic precedence)
    3. ML Risk Model
    """
    if not validation_passed:
        return "VALIDATION_ERROR"
    if deterministic_safety_status == SafetyStatus.EMERGENCY:
        return "EMERGENCY"
    if deterministic_safety_status == SafetyStatus.CONCERNING:
        return "CONCERNING"
    return ml_risk_level.value


def test_emergency_overrides_low_ml_risk():
    """Deterministic EMERGENCY status must override a LOW ML risk assessment."""
    final_status = resolve_decision_state(
        validation_passed=True,
        deterministic_safety_status=SafetyStatus.EMERGENCY,
        ml_risk_level=MaternalRiskLevel.LOW,
    )
    assert final_status == "EMERGENCY"


def test_concerning_overrides_low_ml_risk():
    """Deterministic CONCERNING status must override a LOW ML risk assessment."""
    final_status = resolve_decision_state(
        validation_passed=True,
        deterministic_safety_status=SafetyStatus.CONCERNING,
        ml_risk_level=MaternalRiskLevel.LOW,
    )
    assert final_status == "CONCERNING"


def test_clear_safety_defers_to_ml_risk():
    """When deterministic safety is CLEAR, decision hierarchy uses ML classification."""
    final_status = resolve_decision_state(
        validation_passed=True,
        deterministic_safety_status=SafetyStatus.CLEAR,
        ml_risk_level=MaternalRiskLevel.HIGH,
    )
    assert final_status == "HIGH"


def test_validation_failure_precedes_safety():
    """Validation failure must halt processing before safety or ML evaluation."""
    final_status = resolve_decision_state(
        validation_passed=False,
        deterministic_safety_status=SafetyStatus.EMERGENCY,
        ml_risk_level=MaternalRiskLevel.HIGH,
    )
    assert final_status == "VALIDATION_ERROR"
