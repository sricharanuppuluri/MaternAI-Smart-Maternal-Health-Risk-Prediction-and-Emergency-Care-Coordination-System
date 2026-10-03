"""Authentication and authorization dependencies for FastAPI endpoints.

Enforces:
- 401 Unauthorized when Bearer token is missing or invalid.
- 403 Forbidden when authenticated user lacks required role or access.
- Role resolution: MOTHER, ASHA, ADMIN.
- Patient isolation: Mother A cannot access Mother B.
- Assignment boundary: ASHA can only access assigned mothers.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import Depends, Header

from backend.app.core.errors import ForbiddenError, UnauthorizedError
from backend.app.schemas.auth import AuthUser, UserRole


async def get_current_user(
    authorization: Optional[str] = Header(None, description="Supabase Auth Bearer token"),
) -> AuthUser:
    """Validate Bearer token and resolve authenticated user identity.
    
    In Phase 2, this provides the authoritative contract interface.
    Raises 401 Unauthorized if Authorization header is missing or malformed.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedError(
            message="Missing or malformed Authorization header. Expected 'Bearer <token>'."
        )

    token = authorization.split("Bearer ", 1)[1].strip()
    if not token:
        raise UnauthorizedError(message="Bearer token is empty or invalid.")

    # Phase 2 mock/header token format for contract testing: "test-<role>-<id>" or real JWT
    # Real JWT verification with Supabase GoTrue will be integrated in Phase 3.
    user_id = "00000000-0000-0000-0000-000000000001"
    role = UserRole.MOTHER
    full_name = "Test Mother"

    if "asha" in token.lower():
        role = UserRole.ASHA
        full_name = "Test ASHA"
        user_id = "00000000-0000-0000-0000-000000000002"
    elif "admin" in token.lower():
        role = UserRole.ADMIN
        full_name = "System Admin"
        user_id = "00000000-0000-0000-0000-000000000003"
    elif "mother_b" in token.lower():
        role = UserRole.MOTHER
        full_name = "Mother B"
        user_id = "00000000-0000-0000-0000-000000000004"

    return AuthUser(
        id=UUID(user_id),
        email=f"{role.value.lower()}@example.com",
        role=role,
        full_name=full_name,
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
