"""Safety engine boundaries and status definitions.

Mandatory processing order:
Validation -> Safety Rules -> ML Risk Model -> Decision Layer -> LLM / Agent

Note: Clinical safety thresholds are NOT implemented in Phase 0.
They must be validated against authoritative clinical sources before implementation.
"""

from enum import Enum


class SafetyStatus(str, Enum):
    """Documented safety states for deterministic risk escalation."""
    CLEAR = "CLEAR"
    CONCERNING = "CONCERNING"
    EMERGENCY = "EMERGENCY"
