"""Chat session and message management service (Phase 6).

Enforces:
- Authenticated patient ownership (Mother can only access own chat sessions).
- ASHA assignment boundary (ASHA can only access assigned mothers' sessions).
- Authoritative deterministic safety evaluation (CLEAR, CONCERNING, EMERGENCY).
- Client cannot override, fabricate, or manipulate authoritative safety state.
- Auditability of all chat sessions and message exchanges.
"""

from datetime import datetime, timezone
import re
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

# Emergency keywords indicating acute maternal red flags
EMERGENCY_KEYWORDS = [
    r"\bbleeding\b",
    r"\bhemorrhage\b",
    r"\bconvulsion\b",
    r"\bseizure\b",
    r"\bunconscious\b",
    r"\bchest pain\b",
    r"\bwater broke\b",
    r"\bwater breaking\b",
    r"\bno movement\b",
    r"\breduced movement\b",
    r"\bvision loss\b",
    r"\bblurred vision\b",
]

# Concerning keywords indicating potential maternal complications
CONCERNING_KEYWORDS = [
    r"\bfever\b",
    r"\bchills\b",
    r"\bswelling\b",
    r"\bedema\b",
    r"\bsevere headache\b",
    r"\bheadache\b",
    r"\bvomiting\b",
    r"\bdizziness\b",
    r"\bdizzy\b",
    r"\bpain\b",
    r"\bcramps\b",
    r"\bcramping\b",
]


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
        content: str,
        mother_id: UUID,
    ) -> Tuple[SafetyStatus, List[str], str]:
        """Evaluate message content and clinical context deterministically for safety state."""
        content_lower = content.lower()
        triggered_rules: List[str] = []

        # 1. Deterministic check for emergency text triggers
        for pattern in EMERGENCY_KEYWORDS:
            if re.search(pattern, content_lower):
                matched = pattern.replace(r"\b", "").strip()
                triggered_rules.append(f"Emergency symptom keyword detected: '{matched}'")

        if triggered_rules:
            # Authoritative emergency
            self.repo.add_safety_event(
                mother_id=mother_id,
                safety_status=SafetyStatus.EMERGENCY.value,
                trigger_reason="; ".join(triggered_rules),
                details={"action_required": "Emergency medical evaluation required immediately"},
            )
            guidance = (
                "EMERGENCY ADVISORY: Your message indicates symptoms requiring immediate clinical evaluation. "
                "Please go to the nearest emergency health facility or hospital immediately, or contact emergency medical services. "
                "An urgent safety event has been recorded."
            )
            return SafetyStatus.EMERGENCY, triggered_rules, guidance

        # 2. Deterministic check for concerning text triggers
        for pattern in CONCERNING_KEYWORDS:
            if re.search(pattern, content_lower):
                matched = pattern.replace(r"\b", "").strip()
                triggered_rules.append(f"Concerning symptom keyword detected: '{matched}'")

        if triggered_rules:
            guidance = (
                "CONCERNING SYMPTOM NOTICE: Your report mentions symptoms that warrant prompt attention. "
                "Please consult your assigned ASHA worker or healthcare provider for clinical evaluation."
            )
            return SafetyStatus.CONCERNING, triggered_rules, guidance

        # 3. Clear / Routine maternal guidance
        guidance = (
            "Maternal Care Guidance: Thank you for your message. For routine prenatal care, ensure you attend all scheduled "
            "antenatal checkups, take prescribed supplements (such as iron and folic acid as instructed by your doctor), "
            "stay well-hydrated, and report any new or worsening symptoms promptly."
        )
        return SafetyStatus.CLEAR, [], guidance

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

        # Authoritative safety evaluation (client-submitted safety claims are never trusted)
        safety_status, triggered_rules, assistant_reply = self._evaluate_message_safety(
            payload.content,
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

