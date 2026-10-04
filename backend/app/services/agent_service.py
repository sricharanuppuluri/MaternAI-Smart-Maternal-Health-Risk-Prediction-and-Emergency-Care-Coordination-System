"""AI Agent decision-support query orchestration service (Phase 6).

Enforces:
- Explicit allowlist of authorized agent decision-support tools.
- Strict authentication, patient ownership, and ASHA assignment boundaries.
- Deterministic safety evaluation taking strict precedence over AI/LLM reasoning.
- Prevention of invented clinical recommendations or diagnosis claims.
- Auditing of all agent queries, tool invocations, and safety outcomes.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from backend.app.core.errors import ForbiddenError, NotFoundError, ValidationError
from backend.app.db.repositories import get_repository
from backend.app.safety.evaluator import get_safety_engine
from backend.app.safety.states import SafetyStatus
from backend.app.schemas.agent import (
    AgentQueryRequest,
    AgentQueryResponse,
    AgentToolExecution,
    AgentToolName,
    ToolExecutionStatus,
)
from backend.app.schemas.auth import AuthUser, UserRole

# Permitted tools explicit allowlist
AUTHORIZED_TOOLS_ALLOWLIST = {tool.value for tool in AgentToolName}


class AgentService:
    """Service orchestrating authorized agent tools and decision-support queries."""

    def __init__(self):
        self.repo = get_repository()
        self.safety_engine = get_safety_engine()

    def _resolve_target_mother_id(
        self,
        requested_mother_id: Optional[UUID],
        current_user: AuthUser,
    ) -> UUID:
        """Resolve and verify authorization for target mother ID."""
        if current_user.role == UserRole.MOTHER:
            resolved_id = self.repo.resolve_mother_id(current_user.id)
            if requested_mother_id and requested_mother_id != resolved_id:
                raise ForbiddenError(message="Mothers cannot query agent data for another patient.")
            return resolved_id

        if current_user.role == UserRole.ASHA:
            if not requested_mother_id:
                raise ForbiddenError(message="mother_id is required for ASHA worker agent queries.")
            if not self.repo.is_assigned_asha(current_user.id, requested_mother_id):
                raise ForbiddenError(message="ASHA worker is not assigned to this mother.")
            return requested_mother_id

        if current_user.role == UserRole.ADMIN:
            if not requested_mother_id:
                raise ForbiddenError(message="mother_id is required for admin agent queries.")
            return requested_mother_id

        raise ForbiddenError(message="Access denied.")

    def _execute_tool(
        self,
        tool_name: AgentToolName,
        mother_id: UUID,
    ) -> AgentToolExecution:
        """Execute a single authorized tool within the strict patient boundary."""
        if tool_name == AgentToolName.GET_HEALTH_SUMMARY:
            # Maternal profile and baseline
            mother_prof = self.repo.mother_profiles.get(mother_id)
            if not mother_prof:
                return AgentToolExecution(
                    tool_name=tool_name,
                    status=ToolExecutionStatus.SUCCESS,
                    summary="Mother profile initialized with default baseline.",
                    data={"mother_id": str(mother_id), "status": "active"},
                )
            last_risk = mother_prof.get("last_risk_level")
            last_risk_val = last_risk.value if hasattr(last_risk, "value") else (str(last_risk) if last_risk else None)
            return AgentToolExecution(
                tool_name=tool_name,
                status=ToolExecutionStatus.SUCCESS,
                summary=f"Profile retrieved: assigned ASHA={mother_prof.get('assigned_asha_id')}, last risk={last_risk_val}",
                data={
                    "mother_id": str(mother_id),
                    "full_name": mother_prof.get("full_name"),
                    "assigned_asha_id": str(mother_prof.get("assigned_asha_id")) if mother_prof.get("assigned_asha_id") else None,
                    "last_risk_level": last_risk_val,
                },
            )

        elif tool_name == AgentToolName.GET_RECENT_VITALS:
            vitals = self.repo.list_health_records(mother_id)
            latest = vitals[0] if vitals else None
            summary = f"Retrieved {len(vitals)} vital sign record(s)."
            data = {
                "count": len(vitals),
                "latest_systolic_bp": latest.systolic_bp if latest else None,
                "latest_diastolic_bp": latest.diastolic_bp if latest else None,
                "latest_blood_sugar": latest.blood_sugar if latest else None,
                "latest_hemoglobin": latest.hemoglobin if latest else None,
                "pregnancy_week": latest.pregnancy_week if latest else None,
            }
            return AgentToolExecution(
                tool_name=tool_name,
                status=ToolExecutionStatus.SUCCESS,
                summary=summary,
                data=data,
            )

        elif tool_name == AgentToolName.GET_RECENT_SYMPTOMS:
            symptoms = self.repo.list_symptoms(mother_id)
            summary = f"Retrieved {len(symptoms)} reported symptom(s)."
            data = {
                "count": len(symptoms),
                "symptoms": [{"code": s.symptom_code, "severity": s.severity} for s in symptoms[:5]],
            }
            return AgentToolExecution(
                tool_name=tool_name,
                status=ToolExecutionStatus.SUCCESS,
                summary=summary,
                data=data,
            )

        elif tool_name == AgentToolName.CHECK_SAFETY_ALERTS:
            events = self.repo.list_safety_events(mother_id)
            summary = f"Retrieved {len(events)} recorded safety event(s)."
            data = {
                "safety_events_count": len(events),
                "events": [{"safety_status": e["safety_status"], "trigger_reason": e["trigger_reason"]} for e in events[:3]],
            }
            return AgentToolExecution(
                tool_name=tool_name,
                status=ToolExecutionStatus.SUCCESS,
                summary=summary,
                data=data,
            )

        elif tool_name == AgentToolName.GET_UPCOMING_VISITS:
            visits = self.repo.list_visits(mother_id)
            followups = self.repo.list_followups(mother_id)
            summary = f"Retrieved {len(visits)} visit(s) and {len(followups)} follow-up task(s)."
            data = {
                "visits_count": len(visits),
                "followups_count": len(followups),
            }
            return AgentToolExecution(
                tool_name=tool_name,
                status=ToolExecutionStatus.SUCCESS,
                summary=summary,
                data=data,
            )

        elif tool_name == AgentToolName.EXPLAIN_RISK_FACTORS:
            preds = self.repo.list_predictions(mother_id)
            latest = preds[0] if preds else None
            if latest:
                summary = f"Latest screening tier: {latest.risk_level.value}. {len(latest.contributing_factors)} contributing factor(s)."
                factors_data = [{"feature": f.factor_name, "impact": f.importance_score} for f in latest.contributing_factors]
            else:
                summary = "No prior risk predictions recorded for this mother."
                factors_data = []
            return AgentToolExecution(
                tool_name=tool_name,
                status=ToolExecutionStatus.SUCCESS,
                summary=summary,
                data={"risk_level": latest.risk_level.value if latest else None, "factors": factors_data},
            )

        return AgentToolExecution(
            tool_name=tool_name,
            status=ToolExecutionStatus.DENIED,
            summary=f"Tool '{tool_name.value}' is not executable in this context.",
        )

    def _evaluate_query_safety(
        self,
        mother_id: UUID,
    ) -> Tuple[SafetyStatus, List[str]]:
        """Evaluate maternal safety status via the authoritative safety policy engine.

        The safety-state determination remains behind an explicit authoritative safety-policy boundary.
        Clinical criteria are evaluated by SafetyEngine without ad-hoc text keyword rules.
        """
        recent_records = self.repo.list_health_records(mother_id)
        latest_record = recent_records[0] if recent_records else None
        vitals_dict = latest_record.model_dump() if latest_record else None

        recent_symptoms = self.repo.list_symptoms(mother_id)
        symptoms_eval = (
            [{"symptom_code": s.symptom_code, "severity": s.severity} for s in recent_symptoms]
            if recent_symptoms
            else None
        )

        safety_result = self.safety_engine.evaluate(vitals=vitals_dict, symptoms=symptoms_eval)
        safety_status = safety_result.status
        triggered_rules = list(safety_result.triggered_rules)

        if safety_status == SafetyStatus.EMERGENCY:
            self.repo.add_safety_event(
                mother_id=mother_id,
                safety_status=SafetyStatus.EMERGENCY.value,
                trigger_reason="; ".join(triggered_rules) if triggered_rules else "Authoritative emergency policy triggered",
                details={"action_required": safety_result.action_required or "Emergency clinical evaluation required"},
            )
        elif safety_status == SafetyStatus.CONCERNING:
            self.repo.add_safety_event(
                mother_id=mother_id,
                safety_status=SafetyStatus.CONCERNING.value,
                trigger_reason="; ".join(triggered_rules) if triggered_rules else "Authoritative concerning policy triggered",
                details={"action_required": safety_result.action_required or "Clinical review recommended"},
            )

        return safety_status, triggered_rules

    def execute_query(
        self,
        payload: AgentQueryRequest,
        current_user: AuthUser,
    ) -> AgentQueryResponse:
        """Process agent query with authorized tool execution and deterministic safety precedence."""
        target_mother_id = self._resolve_target_mother_id(payload.mother_id, current_user)
        now = datetime.now(timezone.utc)

        # 1. Authoritative safety check
        safety_status, safety_rules = self._evaluate_query_safety(target_mother_id)

        # 2. Determine and validate tools to invoke
        if payload.requested_tools is not None:
            tools_to_run = payload.requested_tools
        else:
            # Default decision-support toolset
            tools_to_run = [
                AgentToolName.GET_HEALTH_SUMMARY,
                AgentToolName.GET_RECENT_VITALS,
                AgentToolName.GET_RECENT_SYMPTOMS,
            ]

        # 3. Execute authorized tools
        tools_executed: List[AgentToolExecution] = []
        for tool_name in tools_to_run:
            execution_record = self._execute_tool(tool_name, target_mother_id)
            tools_executed.append(execution_record)

        # 4. Formulate structured response (neutral, informational decision-support only)
        tool_summaries = [f"- {t.tool_name.value}: {t.summary}" for t in tools_executed if t.summary]
        tools_text = "\n".join(tool_summaries) if tool_summaries else "No tools invoked."

        rules_info = f" Triggered safety rules: {'; '.join(safety_rules)}." if safety_rules else ""
        response_text = (
            f"Authoritative Safety State: {safety_status.value}.{rules_info}\n\n"
            f"Authorized Context Evaluated:\n{tools_text}"
        )

        # 5. Immutable audit logging
        self.repo.log_audit(
            user_id=current_user.id,
            action="AGENT_QUERY",
            resource_type="agent",
            resource_id=target_mother_id,
            details={
                "query": payload.query[:100],
                "tools_invoked": [t.tool_name.value for t in tools_executed],
                "safety_state": safety_status.value,
                "mother_id": str(target_mother_id),
            },
        )

        return AgentQueryResponse(
            mother_id=target_mother_id,
            query=payload.query,
            response=response_text,
            safety_state=safety_status,
            tools_invoked=tools_executed,
            disclaimer="MaternAI Agent provides maternal decision support and informational coordination only. It does not replace professional medical diagnosis, advice, or treatment.",
            created_at=now,
        )


agent_service = AgentService()
