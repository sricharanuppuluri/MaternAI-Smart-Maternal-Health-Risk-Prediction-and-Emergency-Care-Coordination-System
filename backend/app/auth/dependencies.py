"""Production authentication and authorization dependencies for FastAPI endpoints.

Enforces:
- 401 Unauthorized when Bearer token is missing, malformed, or invalid.
- 403 Forbidden when authenticated user lacks required role or access.
- Role resolution: MOTHER, ASHA, ADMIN.
- Patient isolation: Mother A cannot access Mother B.
- Assignment boundary: ASHA can only access assigned mothers.

Note:
This is the strict production authentication dependency.
Test-specific mock users and token parsers are strictly isolated in testing fixtures
and must NEVER be accepted by this production dependency.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import Depends, Header

from backend.app.core.config import get_settings
from backend.app.core.errors import ForbiddenError, UnauthorizedError
from backend.app.schemas.auth import AuthUser, UserRole


async def get_current_user(
    authorization: Optional[str] = Header(None, description="Supabase Auth Bearer token"),
) -> AuthUser:
    """Validate Supabase JWT Bearer token and resolve authenticated user identity.
    
    Production Authentication Rules:
    - Missing or malformed header -> 401 Unauthorized.
    - Non-JWT or arbitrary string tokens -> 401 Unauthorized.
    - Full cryptographic verification with Supabase GoTrue / public JWKS is scheduled for Phase 3.
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

    # In Phase 2 contract foundation, full Supabase GoTrue public-key validation is deferred to Phase 3.
    # In production without an active Supabase JWT verification service, unverified tokens cannot be accepted.
    if not settings.is_supabase_configured:
        raise UnauthorizedError(
            message="Supabase authentication service is not configured. Production JWT verification required."
        )

    # Cryptographic JWT decoding (Phase 3 production implementation)
    raise UnauthorizedError(
        message="Cryptographic Supabase JWT verification is scheduled for Phase 3. Unverified tokens rejected."
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
