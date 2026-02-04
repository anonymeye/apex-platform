"""Authentication, JWT, and permissions."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Ensure bcrypt is imported and available before creating CryptContext
import bcrypt  # noqa: F401

from apex.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes


# Role-based permission definitions
ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "super_admin": [
        "*",  # All permissions
    ],
    "org_admin": [
        "agents:*",
        "knowledge:*",
        "schemas:*",
        "playbooks:*",
        "tools:*",
        "fine_tuning:*",
        "experiments:*",
        "monitoring:*",
        "org:manage",
        "org:billing",
        "org:members",
        "chat:*",
    ],
    "agent_builder": [
        "agents:create",
        "agents:edit",
        "agents:view",
        "agents:delete",  # Own agents only
        "knowledge:create",
        "knowledge:edit",
        "knowledge:view",
        "schemas:create",
        "schemas:edit",
        "schemas:view",
        "playbooks:create",
        "playbooks:edit",
        "playbooks:view",
        "tools:create",
        "tools:edit",
        "tools:view",
        "monitoring:view",
        "chat:*",
    ],
    "content_manager": [
        "knowledge:create",
        "knowledge:edit",
        "knowledge:delete",
        "knowledge:view",
        "agents:view",  # To see which agents use their content
        "chat:*",
    ],
    "analyst": [
        "monitoring:view",
        "experiments:view",
        "agents:view",
        "knowledge:view",
        "chat:view",
    ],
    "end_user": [
        "chat:send",
        "chat:view_own",
    ],
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def expand_permissions(permissions: List[str]) -> List[str]:
    """Expand wildcard permissions (e.g., 'agents:*' -> all agent permissions)."""
    expanded = set()
    for perm in permissions:
        if perm == "*":
            # Super admin - return all permissions
            return ["*"]
        if perm.endswith(":*"):
            # Resource wildcard - expand to all actions for that resource
            resource = perm[:-2]
            actions = ["create", "edit", "view", "delete"]
            expanded.update([f"{resource}:{action}" for action in actions])
        else:
            expanded.add(perm)
    return list(expanded)


def get_role_permissions(role: str) -> List[str]:
    """Get permissions for a role."""
    return expand_permissions(ROLE_PERMISSIONS.get(role, []))


def has_permission(
    user_permissions: List[str],
    required_permission: str,
    is_super_admin: bool = False,
) -> bool:
    """Check if user has a specific permission."""
    if is_super_admin:
        return True

    expanded_permissions = expand_permissions(user_permissions)

    # Check exact match
    if required_permission in expanded_permissions:
        return True

    # Check wildcard match
    if "*" in expanded_permissions:
        return True

    # Check resource wildcard (e.g., "agents:create" matches "agents:*")
    resource, action = required_permission.split(":", 1)
    if f"{resource}:*" in expanded_permissions:
        return True

    return False


# JWT Token Models
class TokenData(BaseModel):
    """JWT token payload data."""

    sub: str  # user_id
    email: str
    name: Optional[str] = None
    is_super_admin: bool = False
    org_id: str  # Current active organization
    org_role: str  # Role in current organization
    permissions: List[str]  # Flattened permissions
    orgs: List[Dict[str, Any]]  # All organizations user belongs to


def create_access_token(
    user_id: UUID,
    email: str,
    name: Optional[str],
    is_super_admin: bool,
    org_id: UUID,
    org_role: str,
    permissions: List[str],
    orgs: List[Dict[str, Any]],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "sub": str(user_id),
        "email": email,
        "name": name,
        "is_super_admin": is_super_admin,
        "org_id": str(org_id),
        "org_role": org_role,
        "permissions": permissions,
        "orgs": orgs,
        "exp": expire,
        "iat": datetime.utcnow(),
    }

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenData]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenData(**payload)
    except JWTError:
        return None
