"""Chat options schema."""

from typing import Any

from pydantic import BaseModel, Field


class ChatOptions(BaseModel):
    """Options for chat requests."""

    temperature: float | None = Field(None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(None, ge=1)
    top_p: float | None = Field(None, ge=0.0, le=1.0)
    stop: list[str] | None = None
    tools: list[dict[str, Any]] | None = None
    tool_choice: str | dict[str, Any] | None = None
    response_format: dict[str, Any] | None = None
