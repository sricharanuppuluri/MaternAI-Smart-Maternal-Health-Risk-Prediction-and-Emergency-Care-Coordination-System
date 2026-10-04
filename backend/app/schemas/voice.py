"""Pydantic schemas for Multilingual Voice Interaction (Phase 7).

Defines:
- Supported languages enum (VoiceLanguage).
- Technical audio constraints (MIME types, max bytes, max duration).
- Request and response contracts for:
  * Speech-to-Text (/api/v1/voice/transcribe)
  * Voice Confirmation (/api/v1/voice/confirm)
  * Text-to-Speech (/api/v1/voice/synthesize)
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from backend.app.safety.states import SafetyStatus
from backend.app.schemas.chat import ChatTurnResponse


class VoiceLanguage(str, Enum):
    """Explicitly supported multilingual voice language identifiers.
    
    Any language outside this enum is strictly rejected with validation error.
    """
    EN = "en"
    HI = "hi"
    TE = "te"
    TA = "ta"
    KN = "kn"
    BN = "bn"
    MR = "mr"


# Technical audio safety and resource constraints (Non-clinical)
SUPPORTED_AUDIO_MIME_TYPES = [
    "audio/wav",
    "audio/webm",
    "audio/mp3",
    "audio/ogg",
    "audio/m4a",
]

SUPPORTED_TTS_FORMATS = [
    "audio/wav",
    "audio/mp3",
    "audio/ogg",
]

# Max audio payload size: 10 MB decoded audio bytes
MAX_AUDIO_BYTES = 10 * 1024 * 1024

# Max text length for TTS synthesis: 1,000 characters
MAX_TTS_TEXT_LENGTH = 1000

# Max audio duration enforceable: 120 seconds
MAX_AUDIO_DURATION_SECONDS = 120.0


class VoiceTranscriptionRequest(BaseModel):
    """Request schema for speech-to-text audio transcription."""
    model_config = ConfigDict(extra="forbid")

    audio_content: str = Field(
        ...,
        min_length=1,
        description="Base64-encoded audio bytes for speech-to-text processing."
    )
    mime_type: str = Field(
        ...,
        description="MIME type of the audio payload (e.g. 'audio/wav', 'audio/webm', 'audio/mp3', 'audio/ogg', 'audio/m4a')."
    )
    language: VoiceLanguage = Field(
        default=VoiceLanguage.EN,
        description="Expected language identifier code for speech recognition."
    )
    mother_id: Optional[UUID] = Field(
        None,
        description="Optional target mother UUID for patient context. For mothers, defaults to self."
    )
    session_id: Optional[UUID] = Field(
        None,
        description="Optional active chat session UUID to associate transcription context."
    )


class VoiceTranscriptionResponse(BaseModel):
    """Response schema for speech-to-text transcription."""
    model_config = ConfigDict(from_attributes=True)

    transcript: str = Field(
        ...,
        description="Transcribed text output from audio."
    )
    language: VoiceLanguage = Field(
        ...,
        description="Language identifier used for transcription."
    )
    detected_language: VoiceLanguage = Field(
        ...,
        description="Language identifier detected by the STT provider."
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Transcription confidence score (0.0 to 1.0)."
    )
    duration_seconds: float = Field(
        ...,
        ge=0.0,
        description="Processed audio duration in seconds."
    )
    mother_id: Optional[UUID] = Field(
        None,
        description="Target mother UUID if provided or resolved."
    )
    session_id: Optional[UUID] = Field(
        None,
        description="Active chat session UUID if provided."
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when transcription was processed."
    )


class VoiceConfirmationRequest(BaseModel):
    """Request schema for user confirmation of transcribed voice input.
    
    Enforces the Clinical Observation Confirmation Boundary: raw speech transcription
    is never automatically persisted until explicit user confirmation.
    """
    model_config = ConfigDict(extra="forbid")

    session_id: UUID = Field(
        ...,
        description="Target chat session UUID to receive the confirmed message."
    )
    confirmed_text: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Explicitly confirmed text transcript from the user."
    )
    mother_id: Optional[UUID] = Field(
        None,
        description="Optional target mother UUID context."
    )
    language: Optional[VoiceLanguage] = Field(
        default=VoiceLanguage.EN,
        description="Language of the confirmed message."
    )


class VoiceConfirmationResponse(BaseModel):
    """Response schema following explicit user confirmation of voice input."""
    model_config = ConfigDict(from_attributes=True)

    session_id: UUID = Field(
        ...,
        description="Chat session UUID containing the confirmed turn."
    )
    confirmed_text: str = Field(
        ...,
        description="The confirmed text routed into the care session."
    )
    chat_turn: ChatTurnResponse = Field(
        ...,
        description="Completed chat turn with assistant response, disclaimer, and authoritative safety state."
    )
    safety_state: SafetyStatus = Field(
        ...,
        description="Authoritative backend safety state evaluated by SafetyEngine."
    )
    confirmed_at: datetime = Field(
        ...,
        description="Timestamp of user confirmation."
    )


class VoiceSynthesisRequest(BaseModel):
    """Request schema for text-to-speech audio synthesis."""
    model_config = ConfigDict(extra="forbid")

    text: str = Field(
        ...,
        min_length=1,
        max_length=MAX_TTS_TEXT_LENGTH,
        description=f"Text content to convert into speech (max {MAX_TTS_TEXT_LENGTH} characters)."
    )
    language: VoiceLanguage = Field(
        default=VoiceLanguage.EN,
        description="Language identifier for speech synthesis."
    )
    output_format: Optional[str] = Field(
        default="audio/wav",
        description="Desired audio MIME format (e.g. 'audio/wav', 'audio/mp3', 'audio/ogg')."
    )
    mother_id: Optional[UUID] = Field(
        None,
        description="Optional mother UUID for authorization context."
    )


class VoiceSynthesisResponse(BaseModel):
    """Response schema for text-to-speech audio synthesis."""
    model_config = ConfigDict(from_attributes=True)

    audio_content: str = Field(
        ...,
        description="Base64-encoded synthesized audio bytes."
    )
    mime_type: str = Field(
        ...,
        description="Audio MIME type of synthesized content."
    )
    language: VoiceLanguage = Field(
        ...,
        description="Language identifier of synthesized audio."
    )
    text_length: int = Field(
        ...,
        description="Character count of synthesized input text."
    )
    duration_seconds: float = Field(
        ...,
        ge=0.0,
        description="Duration of synthesized audio in seconds."
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp of audio generation."
    )
