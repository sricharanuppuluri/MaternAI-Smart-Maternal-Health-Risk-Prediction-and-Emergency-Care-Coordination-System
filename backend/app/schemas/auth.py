"""Authentication, role definition, and profile onboarding schemas."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class UserRole(str, Enum):
    """Documented user roles for MaternAI.
    
    Role assignment is controlled server-side; client cannot self-elevate.
    """
    MOTHER = "MOTHER"
    ASHA = "ASHA"
    ADMIN = "ADMIN"


class ProfileCreate(BaseModel):
    """Payload to bootstrap or update a user profile after Supabase signup."""
    full_name: str = Field(..., min_length=1, max_length=255)
    role: UserRole = Field(default=UserRole.MOTHER, description="Default role is MOTHER; ADMIN cannot be self-assigned")
    phone: Optional[str] = Field(None, max_length=50)


class ProfileResponse(BaseModel):
    """User profile response."""
    id: UUID
    role: UserRole
    full_name: str
    phone: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AuthUser(BaseModel):
    """Authenticated user context resolved by backend."""
    id: UUID
    email: Optional[str] = None
    role: UserRole
    full_name: str
    phone: Optional[str] = None
    created_at: Optional[datetime] = None
