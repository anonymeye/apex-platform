"""Conversation state (messages + metadata) for Redis-backed session chat."""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)


@dataclass
class ConversationStateMetadata:
    """Metadata for a conversation state."""

    conversation_id: str
    user_id: str
    agent_id: str
    created_at: str  # ISO
    last_activity_at: str  # ISO
    message_count: int


@dataclass
class ConversationState:
    """State for one conversation: messages + metadata."""

    messages: list[dict[str, Any]]  # [{role, content, id?, timestamp?, ...}]
    metadata: ConversationStateMetadata

    def to_dict(self) -> dict[str, Any]:
        """Serialize for Redis (JSON)."""
        return {
            "messages": self.messages,
            "metadata": asdict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConversationState:
        """Deserialize from Redis."""
        meta = data.get("metadata") or {}
        return cls(
            messages=data.get("messages") or [],
            metadata=ConversationStateMetadata(
                conversation_id=str(meta.get("conversation_id", "")),
                user_id=str(meta.get("user_id", "")),
                agent_id=str(meta.get("agent_id", "")),
                created_at=str(meta.get("created_at", "")),
                last_activity_at=str(meta.get("last_activity_at", "")),
                message_count=int(meta.get("message_count", 0)),
            ),
        )


def state_key(user_id: UUID, conversation_id: UUID) -> str:
    """Redis key for one conversation state."""
    return f"user:{user_id}:conversation:{conversation_id}"


def user_pattern(user_id: UUID) -> str:
    """Redis SCAN pattern for all conversation keys of a user."""
    return f"user:{user_id}:*"
