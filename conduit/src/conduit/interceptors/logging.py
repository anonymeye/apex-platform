"""Logging interceptor for request/response logging."""

import logging
from dataclasses import dataclass
from typing import Any

from conduit.interceptors.context import Context


@dataclass
class LoggingInterceptor:
    """Log requests, responses, and errors.

    This interceptor logs all chat requests, responses, and errors using
    Python's logging module. It supports structured logging with metadata.

    Attributes:
        logger: Logger instance to use (defaults to 'conduit')
        log_level: Log level for successful requests (defaults to INFO)
        log_errors: Whether to log errors (defaults to True)
        log_request: Whether to log request details (defaults to True)
        log_response: Whether to log response details (defaults to True)
        include_messages: Whether to include message content in logs
        include_options: Whether to include options in logs

    Examples:
        >>> interceptor = LoggingInterceptor(log_level=logging.DEBUG)
        >>> response = await execute_interceptors(
        ...     model, messages, [interceptor]
        ... )
    """

    logger: logging.Logger | None = None
    log_level: int = logging.INFO
    log_errors: bool = True
    log_request: bool = True
    log_response: bool = True
    include_messages: bool = False
    include_options: bool = False

    def __post_init__(self) -> None:
        """Initialize logger if not provided."""
        if self.logger is None:
            self.logger = logging.getLogger("conduit")

    async def enter(self, ctx: Context) -> Context:
        """Log request details."""
        if self.log_request and self.logger is not None:
            log_data: dict[str, Any] = {
                "model": ctx.model.model_info().model,
                "provider": ctx.model.model_info().provider,
                "message_count": len(ctx.messages),
            }

            if self.include_messages:
                log_data["messages"] = [
                    {"role": msg.role, "content": msg.content} for msg in ctx.messages
                ]

            if self.include_options:
                log_data["options"] = ctx.opts.model_dump(exclude_none=True)

            self.logger.log(self.log_level, "Chat request", extra=log_data)

        return ctx

    async def leave(self, ctx: Context) -> Context:
        """Log response details."""
        if self.log_response and ctx.response and self.logger is not None:
            log_data: dict[str, Any] = {
                "model": ctx.response.model or "unknown",
                "input_tokens": ctx.response.usage.input_tokens,
                "output_tokens": ctx.response.usage.output_tokens,
                "total_tokens": ctx.response.usage.total_tokens or 0,
            }

            if self.include_messages:
                log_data["content"] = ctx.response.extract_content()

            self.logger.log(self.log_level, "Chat response", extra=log_data)

        return ctx

    async def error(self, ctx: Context, error: Exception) -> Context:
        """Log error details."""
        if self.log_errors and self.logger is not None:
            log_data: dict[str, Any] = {
                "error_type": type(error).__name__,
                "error_message": str(error),
            }

            if hasattr(error, "status_code"):
                log_data["status_code"] = error.status_code

            if hasattr(error, "provider"):
                log_data["provider"] = error.provider

            self.logger.error("Chat error", exc_info=error, extra=log_data)

        return ctx
