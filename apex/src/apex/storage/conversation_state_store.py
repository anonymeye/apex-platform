"""Redis-backed store for conversation state (messages + metadata)."""

from __future__ import annotations

import json
import logging
from uuid import UUID

from redis.asyncio import Redis

from apex.storage.conversation_state import (
    ConversationState,
    ConversationStateMetadata,
    state_key,
    user_pattern,
)

logger = logging.getLogger(__name__)


class ConversationStateStore:
    """Get/set/delete conversation state in Redis with TTL."""

    def __init__(self, redis: Redis, ttl_seconds: int = 86400):
        """Initialize store.

        Args:
            redis: Async Redis client.
            ttl_seconds: TTL for state keys (default 1 day). Set on every write.
        """
        self.redis = redis
        self.ttl_seconds = ttl_seconds

    async def get(self, user_id: UUID, conversation_id: UUID) -> ConversationState | None:
        """Load state for a conversation. Returns None if missing."""
        key = state_key(user_id, conversation_id)
        raw = await self.redis.get(key)
        if raw is None:
            return None
        try:
            data = json.loads(raw)
            return ConversationState.from_dict(data)
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning("Invalid conversation state in Redis key %s: %s", key, e)
            await self.redis.delete(key)
            return None

    async def set(self, user_id: UUID, conversation_id: UUID, state: ConversationState) -> None:
        """Save state and set TTL."""
        key = state_key(user_id, conversation_id)
        payload = json.dumps(state.to_dict())
        await self.redis.set(key, payload, ex=self.ttl_seconds)

    async def delete(self, user_id: UUID, conversation_id: UUID) -> None:
        """Delete state for one conversation."""
        key = state_key(user_id, conversation_id)
        await self.redis.delete(key)
        logger.debug("Deleted conversation state: %s", key)

    async def delete_all_for_user(self, user_id: UUID) -> int:
        """Delete all conversation state keys for a user. Returns count deleted."""
        pattern = user_pattern(user_id)
        count = 0
        async for key in self.redis.scan_iter(match=pattern):
            await self.redis.delete(key)
            count += 1
        if count:
            logger.info("Deleted %d conversation state key(s) for user %s", count, user_id)
        return count
