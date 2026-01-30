"""Cache interceptor for response caching."""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from conduit.interceptors.context import Context
from conduit.schema.responses import Response

if TYPE_CHECKING:
    from conduit.schema.messages import Message
    from conduit.schema.options import ChatOptions


@dataclass
class CacheEntry:
    """Cache entry with TTL support."""

    response: Response
    expires_at: datetime | None = None

    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at


@dataclass
class CacheInterceptor:
    """Cache responses to avoid redundant API calls.

    This interceptor caches responses based on a cache key generated from
    messages and options. If a cached response exists and is not expired,
    it returns the cached response without calling the model.

    Attributes:
        ttl: Time-to-live in seconds (None for no expiration)
        cache: Internal cache dictionary (can be shared across instances)
        key_func: Custom function to generate cache keys

    Examples:
        >>> interceptor = CacheInterceptor(ttl=3600)  # 1 hour cache
        >>> response = await execute_interceptors(
        ...     model, messages, [interceptor]
        ... )
    """

    ttl: float | None = None
    cache: dict[str, CacheEntry] = field(default_factory=dict)
    key_func: Any = None  # Callable[[list[Message], ChatOptions], str] | None

    def _generate_key(
        self,
        messages: list["Message"],
        opts: "ChatOptions",
        model_name: str,
    ) -> str:
        """Generate cache key from messages and options.

        Args:
            messages: List of messages
            opts: Chat options
            model_name: Model name

        Returns:
            Cache key string
        """
        if self.key_func:
            result = self.key_func(messages, opts)
            return str(result)  # Ensure it's a string

        # Default key generation
        key_data = {
            "model": model_name,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content if isinstance(msg.content, str) else str(msg.content),
                }
                for msg in messages
            ],
            "options": opts.model_dump(exclude_none=True) if hasattr(opts, "model_dump") else {},
        }

        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()

    async def enter(self, ctx: Context) -> Context:
        """Check cache and return cached response if available."""
        model_name = ctx.model.model_info().model
        cache_key = self._generate_key(ctx.get_messages(), ctx.get_opts(), model_name)

        # Check cache
        if cache_key in self.cache:
            entry = self.cache[cache_key]

            if not entry.is_expired():
                # Return cached response
                ctx.response = entry.response
                ctx.terminated = True
                ctx.metadata["cache_hit"] = True
                return ctx
            else:
                # Remove expired entry
                del self.cache[cache_key]

        ctx.metadata["cache_hit"] = False
        return ctx

    async def leave(self, ctx: Context) -> Context:
        """Store response in cache."""
        if ctx.response and not ctx.metadata.get("cache_hit", False):
            model_name = ctx.model.model_info().model
            cache_key = self._generate_key(ctx.get_messages(), ctx.get_opts(), model_name)

            expires_at = None
            if self.ttl is not None:
                expires_at = datetime.now() + timedelta(seconds=self.ttl)

            self.cache[cache_key] = CacheEntry(response=ctx.response, expires_at=expires_at)

        return ctx
