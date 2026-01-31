"""LLM request/response message logging interceptor for apex."""

import logging
from typing import Any

from conduit.interceptors.context import Context


def _content_preview(content: Any, max_len: int = 400) -> str:
    """Safe string preview of message content."""
    if isinstance(content, str):
        s = content
    else:
        s = str(content)
    if len(s) > max_len:
        return s[:max_len] + "..."
    return s


def _message_summary(msg: Any) -> dict[str, Any]:
    """Summarize a Message for logging."""
    out: dict[str, Any] = {"role": getattr(msg, "role", "?")}
    content = getattr(msg, "content", None)
    if content is not None:
        out["content"] = _content_preview(content)
    if getattr(msg, "tool_call_id", None):
        out["tool_call_id"] = msg.tool_call_id
    tool_calls = getattr(msg, "tool_calls", None)
    if tool_calls:
        out["tool_calls"] = [
            {
                "id": tc.get("id", getattr(tc, "id", "")),
                "name": tc.get("function", {}).get("name", getattr(getattr(tc, "function", None), "name", "")),
            }
            if isinstance(tc, dict)
            else {"id": tc.id, "name": tc.function.name}
            for tc in tool_calls
        ]
    return out


class LLMMessageLoggingInterceptor:
    """Log messages sent to and received from the LLM provider.

    Use with conduit's make_agent(..., interceptors=[...]) so each
    request/response in the agent loop is logged (messages out, response back).
    """

    def __init__(
        self,
        logger: logging.Logger | None = None,
        log_level: int = logging.DEBUG,
        content_max_len: int = 400,
    ):
        self.logger = logger or logging.getLogger(__name__)
        self.log_level = log_level
        self.content_max_len = content_max_len

    async def enter(self, ctx: Context) -> Context:
        """Log outgoing messages to the LLM."""
        messages = ctx.get_messages()
        if not self.logger.isEnabledFor(self.log_level):
            return ctx
        summaries = [_message_summary(m) for m in messages]
        self.logger.log(
            self.log_level,
            "LLM request: %d message(s) -> provider",
            len(messages),
            extra={"llm_messages": summaries},
        )
        for i, m in enumerate(messages):
            role = getattr(m, "role", "?")
            content = getattr(m, "content", None)
            preview = _content_preview(content, self.content_max_len)
            tool_calls = getattr(m, "tool_calls", None)
            if tool_calls:
                names = [
                    tc.get("function", {}).get("name", "?") if isinstance(tc, dict) else getattr(tc.function, "name", "?")
                    for tc in tool_calls
                ]
                self.logger.log(
                    self.log_level,
                    "  [%d] %s: %s | tool_calls=%s",
                    i,
                    role,
                    preview,
                    names,
                )
            else:
                self.logger.log(self.log_level, "  [%d] %s: %s", i, role, preview)
        return ctx

    async def leave(self, ctx: Context) -> Context:
        """Log response from the LLM."""
        if not ctx.response or not self.logger.isEnabledFor(self.log_level):
            return ctx
        content = ctx.response.extract_content()
        preview = _content_preview(content, self.content_max_len)
        tool_calls = getattr(ctx.response, "tool_calls", None)
        if tool_calls:
            names = [getattr(tc.function, "name", "?") for tc in tool_calls]
            self.logger.log(
                self.log_level,
                "LLM response: %s | tool_calls=%s",
                preview,
                names,
            )
        else:
            self.logger.log(self.log_level, "LLM response: %s", preview)
        usage = getattr(ctx.response, "usage", None)
        if usage:
            self.logger.log(
                self.log_level,
                "  usage: in=%s out=%s",
                getattr(usage, "input_tokens", "?"),
                getattr(usage, "output_tokens", "?"),
            )
        return ctx

    async def error(self, ctx: Context, error: Exception) -> Context:
        """Log LLM error."""
        self.logger.error("LLM error: %s", error, exc_info=True)
        return ctx
