"""Tool request/response schemas (top-level tools API)."""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ToolResponse(BaseModel):
    """Schema for tool response (generic Tool)."""

    id: UUID
    name: str
    description: str
    tool_type: str
    knowledge_base_id: Optional[UUID] = None
    config: Optional[dict] = None
    organization_id: UUID
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ToolCreate(BaseModel):
    """Schema for creating a tool (standalone or linked to a knowledge base)."""

    name: str = Field(..., min_length=1, max_length=255, description="Tool name (unique)")
    description: str = Field(..., description="Tool description")
    tool_type: str = Field(..., min_length=1, max_length=50, description="Tool type: rag, api, function, etc.")
    knowledge_base_id: Optional[UUID] = Field(None, description="Link to knowledge base (for RAG tools)")
    config: Optional[dict] = Field(default_factory=dict, description="Type-specific config (e.g. RAG: rag_k, rag_template)")


class ToolUpdate(BaseModel):
    """Schema for updating a tool (generic: name, description, config)."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Tool name")
    description: Optional[str] = Field(None, description="Tool description")
    config: Optional[dict] = Field(None, description="Type-specific config (e.g. RAG: rag_k, rag_template)")
