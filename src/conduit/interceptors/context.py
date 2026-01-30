"""Context for interceptor execution."""

from dataclasses import dataclass, field
from typing import Any

from conduit.core.protocols import ChatModel
from conduit.schema.messages import Message
from conduit.schema.options import ChatOptions
from conduit.schema.responses import Response


@dataclass
class Context:
    """Execution context for interceptor chain.

    Attributes:
        model: The ChatModel instance
        messages: Original messages
        opts: Original options
        response: Response (set after model call)
        transformed_messages: Modified messages (optional)
        transformed_opts: Modified options (optional)
        metadata: Arbitrary metadata shared between interceptors
        terminated: Whether to terminate early
        error: Any error that occurred
    """

    model: ChatModel
    messages: list[Message]
    opts: ChatOptions
    response: Response | None = None
    transformed_messages: list[Message] | None = None
    transformed_opts: ChatOptions | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    terminated: bool = False
    error: Exception | None = None

    def get_messages(self) -> list[Message]:
        """Get messages to use (transformed or original).

        Returns:
            Transformed messages if set, otherwise original messages
        """
        return self.transformed_messages or self.messages

    def get_opts(self) -> ChatOptions:
        """Get options to use (transformed or original).

        Returns:
            Transformed options if set, otherwise original options
        """
        return self.transformed_opts or self.opts
