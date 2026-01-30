"""Message schemas for Conduit."""

from typing import Literal

from pydantic import BaseModel, Field


class TextBlock(BaseModel):
    """Text content block."""

    type: Literal["text"] = "text"
    text: str = Field(..., min_length=1)


class ImageSource(BaseModel):
    """Image source (URL or base64)."""

    type: Literal["url", "base64"]
    url: str | None = None
    data: str | None = None
    media_type: Literal["image/jpeg", "image/png", "image/gif", "image/webp"] | None = None


class ImageBlock(BaseModel):
    """Image content block."""

    type: Literal["image"] = "image"
    source: ImageSource


ContentBlock = str | TextBlock | ImageBlock


class Message(BaseModel):
    """Chat message.

    Examples:
        >>> Message(role="user", content="Hello!")
        >>> Message(role="assistant", content="Hi there!")
    """

    role: Literal["user", "assistant", "system", "tool"]
    content: str | list[ContentBlock]
    name: str | None = None
    tool_call_id: str | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"role": "user", "content": "Hello!"},
                {"role": "assistant", "content": "Hi there!"},
            ]
        }
    }
