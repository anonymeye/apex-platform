"""Pydantic schemas for authentication endpoints."""

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


# Request Schemas
class RegisterRequest(BaseModel):
    """User registration request."""

    email: EmailStr
    password: str
    name: Optional[str] = None
    organization_name: Optional[str] = None  # Auto-create org on registration


class LoginRequest(BaseModel):
    """User login request."""

    email: EmailStr
    password: str


class SwitchOrgRequest(BaseModel):
    """Switch active organization request."""

    org_id: str


# Response Schemas
class OrganizationInfo(BaseModel):
    """Organization information in token."""

    id: str
    name: str
    role: str

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """User information response."""

    id: str
    email: str
    name: Optional[str] = None
    is_super_admin: bool
    current_org_id: str
    current_org_name: Optional[str] = None
    current_role: str
    permissions: List[str]
    organizations: List[OrganizationInfo]

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Authentication token response."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str
