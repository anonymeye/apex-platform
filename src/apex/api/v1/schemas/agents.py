"""Agent request/response schemas."""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ConnectionInfo(BaseModel):
    """Schema for connection information (embedded)."""

    id: UUID
    name: str
    provider: str
    connection_type: str

    class Config:
        from_attributes = True


class ModelRefInfo(BaseModel):
    """Schema for model reference information (embedded)."""

    id: UUID
    name: str
    runtime_id: str
    connection: ConnectionInfo

    class Config:
        from_attributes = True


class AgentCreate(BaseModel):
    """Schema for creating an agent."""

    name: str = Field(..., min_length=1, max_length=255, description="Agent name")
    description: Optional[str] = Field(None, description="Optional agent description")
    model_ref_id: UUID = Field(..., description="Model reference ID to run this agent against")
    system_message: Optional[str] = Field(None, description="System message for the agent")
    max_iterations: int = Field(10, ge=1, le=50, description="Maximum tool-calling iterations")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Model temperature")
    max_tokens: Optional[int] = Field(None, ge=1, description="Maximum tokens in response")
    config: Optional[dict] = Field(default_factory=dict, description="Additional agent configuration")
    tool_ids: Optional[list[UUID]] = Field(
        default_factory=list, description="List of tool IDs to attach to the agent"
    )


class AgentUpdate(BaseModel):
    """Schema for updating an agent."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Agent name")
    description: Optional[str] = Field(None, description="Optional agent description")
    model_ref_id: Optional[UUID] = Field(None, description="Model reference ID")
    system_message: Optional[str] = Field(None, description="System message for the agent")
    max_iterations: Optional[int] = Field(None, ge=1, le=50, description="Maximum tool-calling iterations")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Model temperature")
    max_tokens: Optional[int] = Field(None, ge=1, description="Maximum tokens in response")
    config: Optional[dict] = Field(None, description="Additional agent configuration")
    tool_ids: Optional[list[UUID]] = Field(None, description="List of tool IDs to attach to the agent")


class ToolInfo(BaseModel):
    """Schema for tool information in agent response."""

    id: UUID
    name: str
    description: Optional[str] = None
    tool_type: str

    class Config:
        from_attributes = True


class AgentResponse(BaseModel):
    """Schema for agent response."""

    id: UUID
    name: str
    description: Optional[str] = None
    model_ref_id: UUID
    model_ref: Optional[ModelRefInfo] = None
    system_message: Optional[str] = None
    max_iterations: int
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    config: Optional[dict] = None
    organization_id: UUID
    tools: list[ToolInfo] = Field(default_factory=list, description="List of tools attached to agent")
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True
