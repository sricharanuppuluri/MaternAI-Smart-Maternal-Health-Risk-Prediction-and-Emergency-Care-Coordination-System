"""Deterministic safety evaluation engine and boundary.

Mandatory processing order:
Validation -> Deterministic Safety Rules -> ML Risk Model -> Decision Layer -> Alerts / Workflow

CRITICAL CLINICAL BOUNDARY:
- Do NOT invent clinical thresholds or diagnostic criteria.
- If authoritative clinical rules are provided, they are evaluated deterministically here.
- If no clinical threshold is defined, the engine maintains an explicit extension point
  and defers non-authoritative conditions while returning SafetyStatus.CLEAR.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from backend.app.safety.states import SafetyStatus


@dataclass
class SafetyResult:
    """Outcome of deterministic safety evaluation."""
    status: SafetyStatus
    triggered_rules: List[str] = field(default_factory=list)
    action_required: Optional[str] = None
    is_emergency: bool = False


# Type definition for safety rule evaluator
SafetyRuleFn = Callable[[Optional[Dict[str, Any]], Optional[List[Dict[str, Any]]]], Optional[SafetyResult]]


class SafetyEngine:
    """Deterministic safety evaluation engine executing prior to ML risk prediction."""

    def __init__(self):
        self._rules: List[SafetyRuleFn] = []

    def register_rule(self, rule_fn: SafetyRuleFn):
        """Register a clinical safety rule function.
        
        Clinical teams can register validated clinical threshold rules in Phase 6.
        """
        self._rules.append(rule_fn)

    def clear_rules(self):
        """Clear all registered safety rules (used for test isolation / reset)."""
        self._rules.clear()

    def evaluate(
        self,
        vitals: Optional[Dict[str, Any]] = None,
        symptoms: Optional[List[Dict[str, Any]]] = None,
    ) -> SafetyResult:
        """Evaluate maternal vital signs and symptoms against deterministic safety rules.
        
        Returns:
            SafetyResult with status CLEAR, CONCERNING, or EMERGENCY.
        """
        triggered_rules: List[str] = []
        highest_status = SafetyStatus.CLEAR
        action_required: Optional[str] = None

        # Execute registered deterministic rules
        for rule in self._rules:
            result = rule(vitals, symptoms)
            if result and result.status != SafetyStatus.CLEAR:
                triggered_rules.extend(result.triggered_rules)
                if result.status == SafetyStatus.EMERGENCY:
                    highest_status = SafetyStatus.EMERGENCY
                    action_required = result.action_required or "Immediate clinical escalation required"
                    break  # Emergency terminates further evaluation with top priority
                elif result.status == SafetyStatus.CONCERNING and highest_status != SafetyStatus.EMERGENCY:
                    highest_status = SafetyStatus.CONCERNING
                    action_required = result.action_required or "Follow-up assessment recommended"

        return SafetyResult(
            status=highest_status,
            triggered_rules=triggered_rules,
            action_required=action_required,
            is_emergency=(highest_status == SafetyStatus.EMERGENCY),
        )


# Global safety engine instance
safety_engine = SafetyEngine()


def get_safety_engine() -> SafetyEngine:
    """Dependency provider for deterministic safety engine."""
    return safety_engine
