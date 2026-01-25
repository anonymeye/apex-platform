"""Chat request/response schemas."""

from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Chat request schema."""

    message: str = Field(..., min_length=1, description="User message")
    conversation_id: Optional[UUID] = Field(None, description="Optional conversation ID for continuing a conversation")


class ToolCallResponse(BaseModel):
    """Tool call information in response."""

    id: str
    name: str  # function.name
    arguments: dict[str, Any]  # function.arguments
    result: Optional[Any] = None  # Tool execution result (if available)


class UsageResponse(BaseModel):
    """Token usage information."""

    input_tokens: int
    output_tokens: int
    total_tokens: Optional[int] = None
    cache_read_tokens: Optional[int] = None
    cache_creation_tokens: Optional[int] = None


class ChatResponse(BaseModel):
    """Chat endpoint response."""

    # Main message (matches frontend Message type)
    id: str
    role: Literal["assistant"] = "assistant"
    content: str
    timestamp: str  # ISO format
    tool_calls: Optional[list[ToolCallResponse]] = None

    # Additional metadata
    iterations: int
    usage: Optional[UsageResponse] = None
