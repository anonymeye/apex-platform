"""Connection request/response schemas."""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ConnectionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    connection_type: str = Field(..., min_length=1, max_length=50)  # vendor_api | openai_compatible
    provider: str = Field(..., min_length=1, max_length=50)  # openai | anthropic | groq | openai_compatible
    base_url: Optional[str] = Field(None, max_length=500)
    auth_type: str = Field(..., min_length=1, max_length=50)  # env | bearer | none
    api_key_env_var: Optional[str] = Field(None, max_length=255)
    config: Optional[dict] = Field(default_factory=dict)


class ConnectionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    connection_type: Optional[str] = Field(None, min_length=1, max_length=50)
    provider: Optional[str] = Field(None, min_length=1, max_length=50)
    base_url: Optional[str] = Field(None, max_length=500)
    auth_type: Optional[str] = Field(None, min_length=1, max_length=50)
    api_key_env_var: Optional[str] = Field(None, max_length=255)
    config: Optional[dict] = Field(None)


class ConnectionResponse(BaseModel):
    id: UUID
    name: str
    connection_type: str
    provider: str
    base_url: Optional[str] = None
    auth_type: str
    api_key_env_var: Optional[str] = None
    config: Optional[dict] = None
    organization_id: UUID
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

