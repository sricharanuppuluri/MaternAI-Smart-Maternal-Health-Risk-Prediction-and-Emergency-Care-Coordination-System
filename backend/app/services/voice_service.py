"""Voice processing service orchestrating STT, confirmation, and TTS (Phase 7).

Enforces:
- Clinical Observation Confirmation Boundary: raw speech is never automatically persisted until explicit confirmation.
- Authoritative safety boundary: confirmed speech routes to ChatService and SafetyEngine.
- Patient isolation and ASHA assignment boundaries.
- Provider abstraction isolation: external provider errors never leak internal exceptions or credentials.
- Auditing of all voice operations.
"""

import base64
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from backend.app.core.errors import (
    ForbiddenError,
    NotFoundError,
    ProviderError,
    ValidationError,
)
from backend.app.db.repositories import get_repository
from backend.app.schemas.auth import AuthUser, UserRole
from backend.app.schemas.chat import ChatMessageCreate
from backend.app.schemas.voice import (
    MAX_AUDIO_BYTES,
    MAX_TTS_TEXT_LENGTH,
    SUPPORTED_AUDIO_MIME_TYPES,
    SUPPORTED_TTS_FORMATS,
    VoiceConfirmationRequest,
    VoiceConfirmationResponse,
    VoiceSynthesisRequest,
    VoiceSynthesisResponse,
    VoiceTranscriptionRequest,
    VoiceTranscriptionResponse,
)
from backend.app.services.chat_service import chat_service
from backend.app.voice.providers import get_stt_provider, get_tts_provider


class VoiceService:
    """Service managing speech transcription, user confirmation, and speech synthesis."""

    def __init__(self):
        self.repo = get_repository()

    @property
    def stt_provider(self):
        return get_stt_provider()

    @property
    def tts_provider(self):
        return get_tts_provider()

    def _resolve_target_mother_id(
        self,
        requested_mother_id: Optional[UUID],
        current_user: AuthUser,
        required_for_asha: bool = False,
    ) -> Optional[UUID]:
        """Authorize and resolve target mother ID based on caller role."""
        if current_user.role == UserRole.MOTHER:
            resolved_id = self.repo.resolve_mother_id(current_user.id)
            if requested_mother_id and requested_mother_id != resolved_id:
                raise ForbiddenError(message="Mothers cannot perform voice operations for another patient.")
            return resolved_id

        if current_user.role == UserRole.ASHA:
            if required_for_asha and not requested_mother_id:
                raise ForbiddenError(message="mother_id is required for ASHA worker voice operations.")
            if requested_mother_id and not self.repo.is_assigned_asha(current_user.id, requested_mother_id):
                raise ForbiddenError(message="ASHA worker is not assigned to this mother.")
            return requested_mother_id

        if current_user.role == UserRole.ADMIN:
            return requested_mother_id

        raise ForbiddenError(message="Access denied.")

    def transcribe(
        self,
        payload: VoiceTranscriptionRequest,
        current_user: AuthUser,
    ) -> VoiceTranscriptionResponse:
        """Transcribe base64-encoded audio bytes to text without committing clinical data."""
        # 1. Authorize patient context if specified
        target_mother_id = self._resolve_target_mother_id(
            payload.mother_id,
            current_user,
            required_for_asha=False,
        )

        # 2. Validate session context if provided
        if payload.session_id:
            session = self.repo.get_chat_session(payload.session_id)
            if not session:
                raise NotFoundError(message=f"Chat session with id '{payload.session_id}' was not found.")
            session_mother_id = session["mother_id"]
            if current_user.role == UserRole.MOTHER and session_mother_id != self.repo.resolve_mother_id(current_user.id):
                raise ForbiddenError(message="Mothers cannot access another patient's chat session.")
            if current_user.role == UserRole.ASHA and not self.repo.is_assigned_asha(current_user.id, session_mother_id):
                raise ForbiddenError(message="ASHA worker is not assigned to this mother.")

        # 3. Validate audio MIME type
        if payload.mime_type not in SUPPORTED_AUDIO_MIME_TYPES:
            raise ValidationError(
                message=f"Unsupported audio MIME type '{payload.mime_type}'. Supported types: {', '.join(SUPPORTED_AUDIO_MIME_TYPES)}."
            )

        # 4. Decode base64 audio content
        try:
            audio_bytes = base64.b64decode(payload.audio_content, validate=True)
        except Exception:
            raise ValidationError(message="Invalid base64 encoding for audio_content.")

        # 5. Validate audio payload size
        if len(audio_bytes) == 0:
            raise ValidationError(message="Audio content cannot be empty.")
        if len(audio_bytes) > MAX_AUDIO_BYTES:
            max_mb = MAX_AUDIO_BYTES // (1024 * 1024)
            raise ValidationError(message=f"Audio payload size ({len(audio_bytes)} bytes) exceeds maximum limit of {max_mb} MB.")

        # 6. Execute Speech-to-Text provider
        try:
            stt_result = self.stt_provider.transcribe(
                audio_bytes=audio_bytes,
                mime_type=payload.mime_type,
                language=payload.language,
            )
        except Exception as e:
            # Mask internal/provider exception details from client
            raise ProviderError(message="Speech-to-text provider failed to transcribe audio.") from e

        now = datetime.now(timezone.utc)

        # 7. Audit log (raw speech is never persisted as clinical record)
        self.repo.log_audit(
            user_id=current_user.id,
            action="VOICE_TRANSCRIBE",
            resource_type="voice",
            resource_id=target_mother_id or current_user.id,
            details={
                "language": payload.language.value,
                "mime_type": payload.mime_type,
                "duration_seconds": stt_result.duration_seconds,
                "session_id": str(payload.session_id) if payload.session_id else None,
            },
        )

        return VoiceTranscriptionResponse(
            transcript=stt_result.transcript,
            language=stt_result.language,
            detected_language=stt_result.detected_language,
            confidence=stt_result.confidence,
            duration_seconds=stt_result.duration_seconds,
            mother_id=target_mother_id,
            session_id=payload.session_id,
            created_at=now,
        )

    def confirm(
        self,
        payload: VoiceConfirmationRequest,
        current_user: AuthUser,
    ) -> VoiceConfirmationResponse:
        """Confirm transcribed voice input and route into authoritative chat and safety workflow."""
        # 1. Verify target session existence
        session = self.repo.get_chat_session(payload.session_id)
        if not session:
            raise NotFoundError(message=f"Chat session with id '{payload.session_id}' was not found.")

        session_mother_id = session["mother_id"]

        # 2. Enforce patient ownership and ASHA assignment boundaries
        if current_user.role == UserRole.MOTHER:
            resolved_id = self.repo.resolve_mother_id(current_user.id)
            if session_mother_id != resolved_id:
                raise ForbiddenError(message="Mothers cannot confirm messages into another patient's chat session.")
        elif current_user.role == UserRole.ASHA:
            if not self.repo.is_assigned_asha(current_user.id, session_mother_id):
                raise ForbiddenError(message="ASHA worker is not assigned to this mother.")
        elif current_user.role != UserRole.ADMIN:
            raise ForbiddenError(message="Access denied.")

        # 3. Route confirmed text through authoritative chat service (enforces SafetyEngine boundary)
        msg_payload = ChatMessageCreate(
            content=payload.confirmed_text,
            language=payload.language.value if payload.language else "en",
        )
        chat_turn = chat_service.send_message(payload.session_id, msg_payload, current_user)

        now = datetime.now(timezone.utc)

        # 4. Audit logging
        self.repo.log_audit(
            user_id=current_user.id,
            action="VOICE_CONFIRM",
            resource_type="voice",
            resource_id=session_mother_id,
            details={
                "session_id": str(payload.session_id),
                "safety_state": chat_turn.safety_state.value,
            },
        )

        return VoiceConfirmationResponse(
            session_id=payload.session_id,
            confirmed_text=payload.confirmed_text,
            chat_turn=chat_turn,
            safety_state=chat_turn.safety_state,
            confirmed_at=now,
        )

    def synthesize(
        self,
        payload: VoiceSynthesisRequest,
        current_user: AuthUser,
    ) -> VoiceSynthesisResponse:
        """Synthesize text into speech audio bytes for playback UI."""
        # 1. Authorize patient context if specified
        target_mother_id = self._resolve_target_mother_id(
            payload.mother_id,
            current_user,
            required_for_asha=False,
        )

        # 2. Validate input text
        cleaned_text = payload.text.strip()
        if not cleaned_text:
            raise ValidationError(message="Text content cannot be empty.")
        if len(cleaned_text) > MAX_TTS_TEXT_LENGTH:
            raise ValidationError(message=f"Text content exceeds maximum allowed length of {MAX_TTS_TEXT_LENGTH} characters.")

        # 3. Validate output audio format
        out_format = payload.output_format or "audio/wav"
        if out_format not in SUPPORTED_TTS_FORMATS:
            raise ValidationError(
                message=f"Unsupported output format '{out_format}'. Supported formats: {', '.join(SUPPORTED_TTS_FORMATS)}."
            )

        # 4. Execute Text-to-Speech provider
        try:
            tts_result = self.tts_provider.synthesize(
                text=cleaned_text,
                language=payload.language,
                output_format=out_format,
            )
        except Exception as e:
            # Mask internal/provider exception details from client
            raise ProviderError(message="Text-to-speech provider failed to synthesize audio.") from e

        # 5. Base64 encode synthesized audio
        audio_base64 = base64.b64encode(tts_result.audio_bytes).decode("ascii")
        now = datetime.now(timezone.utc)

        # 6. Audit log
        self.repo.log_audit(
            user_id=current_user.id,
            action="VOICE_SYNTHESIZE",
            resource_type="voice",
            resource_id=target_mother_id or current_user.id,
            details={
                "language": payload.language.value,
                "output_format": out_format,
                "text_length": len(cleaned_text),
            },
        )

        return VoiceSynthesisResponse(
            audio_content=audio_base64,
            mime_type=tts_result.mime_type,
            language=tts_result.language,
            text_length=len(cleaned_text),
            duration_seconds=tts_result.duration_seconds,
            created_at=now,
        )


voice_service = VoiceService()
