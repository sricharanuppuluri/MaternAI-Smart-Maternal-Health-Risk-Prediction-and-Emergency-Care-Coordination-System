"""Pydantic schemas for Chat Sessions and Messages (Phase 6)."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from backend.app.safety.states import SafetyStatus


class MessageSenderRole(str, Enum):
    """Permitted roles for chat message senders."""
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    SYSTEM = "SYSTEM"


class ChatSessionCreate(BaseModel):
    """Request schema for creating a new chat session."""
    model_config = ConfigDict(extra="forbid")

    mother_id: Optional[UUID] = Field(
        None,
        description="Target mother UUID. For mothers, defaults to authenticated self. For ASHAs, must be an assigned mother."
    )
    title: Optional[str] = Field(
        None,
        max_length=100,
        description="Optional title or topic for the chat session."
    )
    language: Optional[str] = Field(
        "en",
        max_length=10,
        description="Preferred language code (e.g. 'en', 'hi', 'te', 'ta')."
    )


class ChatSessionResponse(BaseModel):
    """Response schema for a chat session."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    mother_id: UUID
    title: Optional[str] = None
    language: str = "en"
    created_at: datetime


class ChatMessageCreate(BaseModel):
    """Request schema for submitting a message to a chat session."""
    model_config = ConfigDict(extra="forbid")

    content: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User text message content. Non-empty string."
    )
    language: Optional[str] = Field(
        "en",
        max_length=10,
        description="Language code for the message."
    )


class MessageItem(BaseModel):
    """Structure of an individual message within a chat turn."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    sender_role: MessageSenderRole
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ChatTurnResponse(BaseModel):
    """Structured response schema for a completed chat message turn."""
    model_config = ConfigDict(from_attributes=True)

    session_id: UUID
    user_message: MessageItem
    assistant_message: MessageItem
    safety_state: SafetyStatus = Field(
        ...,
        description="Authoritative backend safety state: CLEAR, CONCERNING, or EMERGENCY. Never client-controlled."
    )
    safety_events: List[str] = Field(
        default_factory=list,
        description="List of deterministic safety rule trigger descriptions, if any."
    )
    disclaimer: str = Field(
        default="MaternAI provides maternal decision support and educational guidance only. It does not replace professional medical diagnosis, advice, or treatment."
    )
