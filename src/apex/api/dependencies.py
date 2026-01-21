"""Dependency injection for FastAPI."""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from apex.core.security import decode_access_token
from apex.models.user import User

security = HTTPBearer()


async def get_current_user_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Extract JWT token from Authorization header."""
    return credentials.credentials


async def get_current_user_from_token(
    token: str = Depends(get_current_user_token),
) -> dict:
    """Decode and validate JWT token, return token data."""
    token_data = decode_access_token(token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data.dict()


# Note: Actual database session and user fetching should be implemented
# based on your database setup. This is a placeholder structure.
