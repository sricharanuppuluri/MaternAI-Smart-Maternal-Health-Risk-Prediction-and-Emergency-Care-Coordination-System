"""Pydantic schemas for AI Agent Decision-Support Queries (Phase 6)."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from backend.app.safety.states import SafetyStatus


class AgentToolName(str, Enum):
    """Explicit allowlist of permitted agent decision-support tools.

    Any tool not in this allowlist is strictly prohibited and rejected.
    """
    GET_HEALTH_SUMMARY = "get_health_summary"
    GET_RECENT_VITALS = "get_recent_vitals"
    GET_RECENT_SYMPTOMS = "get_recent_symptoms"
    CHECK_SAFETY_ALERTS = "check_safety_alerts"
    GET_UPCOMING_VISITS = "get_upcoming_visits"
    EXPLAIN_RISK_FACTORS = "explain_risk_factors"


class ToolExecutionStatus(str, Enum):
    """Execution status for an authorized agent tool."""
    SUCCESS = "SUCCESS"
    SKIPPED = "SKIPPED"
    DENIED = "DENIED"


class AgentToolExecution(BaseModel):
    """Structured execution record for an authorized tool invocation."""
    model_config = ConfigDict(from_attributes=True)

    tool_name: AgentToolName
    status: ToolExecutionStatus
    summary: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class AgentQueryRequest(BaseModel):
    """Request schema for querying the MaternAI decision-support agent."""
    model_config = ConfigDict(extra="forbid")

    mother_id: Optional[UUID] = Field(
        None,
        description="Target mother UUID. For mothers, defaults to authenticated self. For ASHAs, must be an assigned mother."
    )
    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Clinical query or question for the decision-support agent."
    )
    requested_tools: Optional[List[AgentToolName]] = Field(
        None,
        description="Optional list of specific authorized tools to invoke. Must be in AgentToolName allowlist."
    )
    language: Optional[str] = Field(
        "en",
        max_length=10,
        description="Language code for agent query and response."
    )


class AgentQueryResponse(BaseModel):
    """Structured response schema for an agent decision-support query."""
    model_config = ConfigDict(from_attributes=True)

    mother_id: UUID
    query: str
    response: str
    safety_state: SafetyStatus = Field(
        ...,
        description="Authoritative safety state: CLEAR, CONCERNING, or EMERGENCY. Overrides agent reasoning."
    )
    tools_invoked: List[AgentToolExecution] = Field(
        default_factory=list,
        description="Audit list of authorized tools executed during query processing."
    )
    disclaimer: str = Field(
        default="MaternAI Agent provides maternal decision support and informational coordination only. It does not replace professional medical diagnosis, advice, or treatment."
    )
    created_at: datetime
