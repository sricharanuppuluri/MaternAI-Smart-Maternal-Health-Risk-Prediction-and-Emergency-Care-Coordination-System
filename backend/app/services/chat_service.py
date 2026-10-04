"""Chat session and message management service (Phase 6).

Enforces:
- Authenticated patient ownership (Mother can only access own chat sessions).
- ASHA assignment boundary (ASHA can only access assigned mothers' sessions).
- Authoritative deterministic safety evaluation (CLEAR, CONCERNING, EMERGENCY) via backend safety engine.
- Client cannot override, fabricate, or manipulate authoritative safety state.
- Absence of unapproved symptom keyword heuristics or invented clinical guidance.
- Auditability of all chat sessions and message exchanges.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from backend.app.core.errors import ForbiddenError, NotFoundError, ValidationError
from backend.app.db.repositories import get_repository
from backend.app.safety.evaluator import get_safety_engine
from backend.app.safety.states import SafetyStatus
from backend.app.schemas.auth import AuthUser, UserRole
from backend.app.schemas.chat import (
    ChatMessageCreate,
    ChatSessionCreate,
    ChatSessionResponse,
    ChatTurnResponse,
    MessageItem,
    MessageSenderRole,
)


class ChatService:
    """Service handling maternal chat sessions, messages, and authoritative safety evaluation."""

    def __init__(self):
        self.repo = get_repository()
        self.safety_engine = get_safety_engine()

    def _resolve_target_mother_id(
        self,
        requested_mother_id: Optional[UUID],
        current_user: AuthUser,
    ) -> UUID:
        """Resolve and authorize target mother ID based on caller role."""
        if current_user.role == UserRole.MOTHER:
            resolved_id = self.repo.resolve_mother_id(current_user.id)
            if requested_mother_id and requested_mother_id != resolved_id:
                raise ForbiddenError(message="Mothers can only create or access sessions for themselves.")
            return resolved_id

        if current_user.role == UserRole.ASHA:
            if not requested_mother_id:
                raise ForbiddenError(message="mother_id is required for ASHA worker chat session operations.")
            if not self.repo.is_assigned_asha(current_user.id, requested_mother_id):
                raise ForbiddenError(message="ASHA worker is not assigned to this mother.")
            return requested_mother_id

        if current_user.role == UserRole.ADMIN:
            if not requested_mother_id:
                raise ForbiddenError(message="mother_id is required to create a chat session.")
            return requested_mother_id

        raise ForbiddenError(message="Access denied.")

    def create_session(
        self,
        payload: ChatSessionCreate,
        current_user: AuthUser,
    ) -> ChatSessionResponse:
        """Create a new chat session for an authorized mother."""
        target_mother_id = self._resolve_target_mother_id(payload.mother_id, current_user)
        session_id = uuid4()
        now = datetime.now(timezone.utc)

        self.repo.create_chat_session(
            session_id=session_id,
            mother_id=target_mother_id,
            created_at=now,
        )

        self.repo.log_audit(
            user_id=current_user.id,
            action="CREATE_CHAT_SESSION",
            resource_type="chat_sessions",
            resource_id=session_id,
            details={"mother_id": str(target_mother_id), "language": payload.language or "en"},
        )

        return ChatSessionResponse(
            id=session_id,
            mother_id=target_mother_id,
            title=payload.title,
            language=payload.language or "en",
            created_at=now,
        )

    def _evaluate_message_safety(
        self,
        mother_id: UUID,
    ) -> Tuple[SafetyStatus, List[str], str]:
        """Evaluate maternal safety status via the authoritative safety policy engine.

        The safety-state determination remains behind an explicit authoritative safety-policy boundary.
        Clinical criteria are not fabricated or inferred from text keywords.
        Where clinical policy is pending authoritative specification, the engine deterministically
        returns CLEAR while preserving the extension boundary for validated rules.
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
            reply = (
                "Authoritative safety state: EMERGENCY. "
                f"Triggered clinical safety rules: {'; '.join(triggered_rules) if triggered_rules else 'Authoritative emergency policy triggered.'}"
            )
        elif safety_status == SafetyStatus.CONCERNING:
            self.repo.add_safety_event(
                mother_id=mother_id,
                safety_status=SafetyStatus.CONCERNING.value,
                trigger_reason="; ".join(triggered_rules) if triggered_rules else "Authoritative concerning policy triggered",
                details={"action_required": safety_result.action_required or "Clinical review recommended"},
            )
            reply = (
                "Authoritative safety state: CONCERNING. "
                f"Triggered clinical safety rules: {'; '.join(triggered_rules) if triggered_rules else 'Authoritative concerning policy triggered.'}"
            )
        else:
            reply = (
                "Authoritative safety state: CLEAR. "
                "Message received and logged in care session. Detailed clinical safety policy is pending authoritative specification."
            )

        return safety_status, triggered_rules, reply

    def send_message(
        self,
        session_id: UUID,
        payload: ChatMessageCreate,
        current_user: AuthUser,
    ) -> ChatTurnResponse:
        """Submit a user message to a chat session, evaluate safety, and return the assistant response."""
        session = self.repo.get_chat_session(session_id)
        if not session:
            raise NotFoundError(message=f"Chat session with id '{session_id}' was not found.")

        session_mother_id = session["mother_id"]

        # Enforce patient isolation / ASHA assignment boundary
        if current_user.role == UserRole.MOTHER:
            resolved_id = self.repo.resolve_mother_id(current_user.id)
            if session_mother_id != resolved_id:
                raise ForbiddenError(message="Mothers cannot access another patient's chat session.")
        elif current_user.role == UserRole.ASHA:
            if not self.repo.is_assigned_asha(current_user.id, session_mother_id):
                raise ForbiddenError(message="ASHA worker is not assigned to this mother.")
        elif current_user.role != UserRole.ADMIN:
            raise ForbiddenError(message="Access denied.")

        now = datetime.now(timezone.utc)

        # Authoritative safety evaluation (client-submitted claims are never trusted)
        safety_status, triggered_rules, assistant_reply = self._evaluate_message_safety(
            session_mother_id,
        )

        # Record User Message
        user_msg_id = uuid4()
        user_meta = {"language": payload.language or "en", "authoritative_safety_state": safety_status.value}
        self.repo.add_chat_message(
            message_id=user_msg_id,
            session_id=session_id,
            sender_role=MessageSenderRole.USER.value,
            content=payload.content,
            metadata=user_meta,
            created_at=now,
        )

        # Record Assistant Message
        asst_msg_id = uuid4()
        asst_meta = {"safety_state": safety_status.value, "language": payload.language or "en"}
        self.repo.add_chat_message(
            message_id=asst_msg_id,
            session_id=session_id,
            sender_role=MessageSenderRole.ASSISTANT.value,
            content=assistant_reply,
            metadata=asst_meta,
            created_at=now,
        )

        # Audit trail
        self.repo.log_audit(
            user_id=current_user.id,
            action="CREATE_CHAT_MESSAGE",
            resource_type="chat_messages",
            resource_id=user_msg_id,
            details={
                "session_id": str(session_id),
                "mother_id": str(session_mother_id),
                "safety_state": safety_status.value,
            },
        )

        user_item = MessageItem(
            id=user_msg_id,
            session_id=session_id,
            sender_role=MessageSenderRole.USER,
            content=payload.content,
            metadata=user_meta,
            created_at=now,
        )

        asst_item = MessageItem(
            id=asst_msg_id,
            session_id=session_id,
            sender_role=MessageSenderRole.ASSISTANT,
            content=assistant_reply,
            metadata=asst_meta,
            created_at=now,
        )

        return ChatTurnResponse(
            session_id=session_id,
            user_message=user_item,
            assistant_message=asst_item,
            safety_state=safety_status,
            safety_events=triggered_rules,
            disclaimer="MaternAI provides maternal decision support and educational guidance only. It does not replace professional medical diagnosis, advice, or treatment.",
        )


chat_service = ChatService()
