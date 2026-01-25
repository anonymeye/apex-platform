"""Model reference request/response schemas."""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from apex.api.v1.schemas.connections import ConnectionResponse


class ModelRefCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    runtime_id: str = Field(..., min_length=1, max_length=255)
    connection_id: UUID
    config: Optional[dict] = Field(default_factory=dict)


class ModelRefUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    runtime_id: Optional[str] = Field(None, min_length=1, max_length=255)
    connection_id: Optional[UUID] = None
    config: Optional[dict] = None


class ModelRefResponse(BaseModel):
    id: UUID
    name: str
    runtime_id: str
    config: Optional[dict] = None
    connection_id: UUID
    connection: Optional[ConnectionResponse] = None
    organization_id: UUID
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

