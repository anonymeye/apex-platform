"""Response schemas for Conduit."""

from typing import Any, Literal

from pydantic import BaseModel, Field

from conduit.schema.messages import ContentBlock, TextBlock


class Usage(BaseModel):
    """Token usage information."""

    input_tokens: int = Field(..., ge=0)
    output_tokens: int = Field(..., ge=0)
    total_tokens: int | None = Field(None, ge=0)
    cache_read_tokens: int | None = Field(None, ge=0)
    cache_creation_tokens: int | None = Field(None, ge=0)


class FunctionCall(BaseModel):
    """Function call details."""

    name: str
    arguments: dict[str, Any]


class ToolCall(BaseModel):
    """Tool invocation requested by the model."""

    id: str
    type: Literal["function"] = "function"
    function: FunctionCall


class Response(BaseModel):
    """Unified response format from all providers."""

    id: str | None = None
    role: Literal["assistant"] = "assistant"
    content: str | list[ContentBlock]
    model: str | None = None
    stop_reason: (
        Literal["end_turn", "tool_use", "max_tokens", "stop_sequence", "content_filter"] | None
    ) = None
    usage: Usage
    tool_calls: list[ToolCall] | None = None

    def extract_content(self) -> str:
        """Extract text content from response."""
        if isinstance(self.content, str):
            return self.content

        texts = []
        for block in self.content:
            if isinstance(block, str):
                texts.append(block)
            elif isinstance(block, TextBlock):
                texts.append(block.text)
        return "".join(texts)
