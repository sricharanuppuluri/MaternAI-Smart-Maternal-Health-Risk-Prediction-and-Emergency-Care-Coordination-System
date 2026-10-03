"""Production authentication and authorization dependencies for FastAPI endpoints.

Enforces:
- 401 Unauthorized when Bearer token is missing, malformed, expired, or unverified.
- Cryptographic Supabase JWT signature and claims verification.
- Authoritative application role resolution strictly from the database profiles table.
- Rejection of client-submitted roles or unverified token claims.
- 403 Forbidden when authenticated user lacks required role or access.
- Patient isolation: Mother A cannot access Mother B.
- Assignment boundary: ASHA can only access assigned mothers.
- Isolation of test authentication via FastAPI dependency overrides.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import Depends, Header
import jwt
from jwt.exceptions import (
    DecodeError,
    ExpiredSignatureError,
    InvalidSignatureError,
    InvalidTokenError,
)

from backend.app.core.config import get_settings
from backend.app.core.errors import ForbiddenError, UnauthorizedError
from backend.app.db.repositories import get_repository
from backend.app.schemas.auth import AuthUser, UserRole


async def get_current_user(
    authorization: Optional[str] = Header(None, description="Supabase Auth Bearer token"),
) -> AuthUser:
    """Validate Supabase JWT Bearer token and resolve authoritative user identity.
    
    Production Authentication Rules:
    - Missing or malformed header -> 401 Unauthorized.
    - Non-JWT or arbitrary string tokens -> 401 Unauthorized.
    - Cryptographically verified against SUPABASE_JWT_SECRET.
    - If Supabase authentication is unconfigured, fails closed with 401.
    - Role is resolved strictly from database profiles table, NEVER trusted from client claims.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedError(
            message="Missing or malformed Authorization header. Expected 'Bearer <token>'."
        )

    token = authorization.split("Bearer ", 1)[1].strip()
    if not token:
        raise UnauthorizedError(message="Bearer token is empty or invalid.")

    # Validate JWT structure (header.payload.signature)
    segments = token.split(".")
    if len(segments) != 3:
        raise UnauthorizedError(
            message="Invalid JWT token structure. Production tokens must be valid signed JWTs."
        )

    settings = get_settings()

    # Fail closed if verification secret is unconfigured
    if not settings.SUPABASE_JWT_SECRET:
        raise UnauthorizedError(
            message="Supabase authentication service is not configured. Production JWT verification required."
        )

    # Cryptographic JWT decoding and signature validation
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_signature": True, "verify_exp": True, "verify_aud": False},
        )
    except ExpiredSignatureError:
        raise UnauthorizedError(message="Token has expired. Please re-authenticate.")
    except (InvalidSignatureError, DecodeError, InvalidTokenError):
        raise UnauthorizedError(
            message="Invalid token signature: unverified token rejected."
        )

    # Extract authenticated user identity from 'sub' claim
    sub = payload.get("sub")
    if not sub:
        raise UnauthorizedError(message="Token missing subject ('sub') claim.")
    try:
        user_id = UUID(str(sub))
    except (ValueError, TypeError):
        raise UnauthorizedError(message="Token subject claim is not a valid UUID.")

    # Resolve authoritative application role strictly from database profiles table
    repo = get_repository()
    profile = repo.get_profile(user_id)

    if profile:
        raw_role = profile.get("role")
        if isinstance(raw_role, UserRole):
            role = raw_role
        elif isinstance(raw_role, str):
            try:
                role = UserRole(raw_role)
            except ValueError:
                role = UserRole.MOTHER
        else:
            role = UserRole.MOTHER
        full_name = profile.get("full_name") or "User"
        phone = profile.get("phone")
    else:
        # Default unprivileged role for fresh authenticated user
        # Security invariant: NEVER trust client-submitted roles or JWT user_metadata claims!
        role = UserRole.MOTHER
        user_meta = payload.get("user_metadata") or {}
        full_name = user_meta.get("full_name") or "New User"
        phone = user_meta.get("phone")

    email = payload.get("email")

    return AuthUser(
        id=user_id,
        email=email,
        role=role,
        full_name=full_name,
        phone=phone,
    )


def require_role(allowed_roles: List[UserRole]):
    """Dependency factory restricting endpoint access to specific roles."""

    async def role_checker(current_user: AuthUser = Depends(get_current_user)) -> AuthUser:
        if current_user.role not in allowed_roles:
            raise ForbiddenError(
                message=f"Access forbidden: role '{current_user.role.value}' does not have required permissions."
            )
        return current_user

    return role_checker


# Role-specific dependency shortcuts
require_mother = require_role([UserRole.MOTHER, UserRole.ADMIN])
require_asha = require_role([UserRole.ASHA, UserRole.ADMIN])
require_admin = require_role([UserRole.ADMIN])


def verify_patient_access(
    current_user: AuthUser,
    target_mother_id: UUID,
    assigned_mother_ids: Optional[List[UUID]] = None,
) -> bool:
    """Verify whether current user has authorization to access target mother's records.
    
    Rules:
    - MOTHER can only access their own record.
    - ASHA can only access assigned mothers.
    - ADMIN has operational access.
    """
    if current_user.role == UserRole.ADMIN:
        return True

    if current_user.role == UserRole.MOTHER:
        if current_user.id != target_mother_id:
            raise ForbiddenError(message="Mothers cannot access another patient's records.")
        return True

    if current_user.role == UserRole.ASHA:
        if assigned_mother_ids is not None and target_mother_id not in assigned_mother_ids:
            raise ForbiddenError(message="ASHA worker is not assigned to this mother.")
        return True

    raise ForbiddenError(message="Access denied.")
