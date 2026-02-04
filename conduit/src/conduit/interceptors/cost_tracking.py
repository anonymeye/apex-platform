"""Cost tracking interceptor for monitoring API costs."""

from collections.abc import Callable
from dataclasses import dataclass, field

from conduit.interceptors.context import Context

# Default pricing per 1M tokens (in USD)
DEFAULT_PRICING: dict[str, dict[str, dict[str, float]]] = {
    "openai": {
        "gpt-4": {"input": 30.0, "output": 60.0},
        "gpt-4-turbo": {"input": 10.0, "output": 30.0},
        "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
    },
    "anthropic": {
        "claude-3-opus": {"input": 15.0, "output": 75.0},
        "claude-3-sonnet": {"input": 3.0, "output": 15.0},
        "claude-3-haiku": {"input": 0.25, "output": 1.25},
    },
}


@dataclass
class CostTrackingInterceptor:
    """Track API costs for chat requests.

    This interceptor tracks token usage and calculates costs based on
    provider-specific pricing. It can call a callback function with cost
    information after each request.

    Attributes:
        pricing: Pricing dictionary mapping provider -> model -> input/output prices
        on_cost: Callback function called with cost information
        total_cost: Running total of costs (in USD)
        request_count: Number of requests tracked

    Examples:
        >>> def log_cost(cost: float, tokens: dict):
        ...     print(f"Cost: ${cost:.4f}, Tokens: {tokens}")
        >>>
        >>> interceptor = CostTrackingInterceptor(on_cost=log_cost)
        >>> response = await execute_interceptors(
        ...     model, messages, [interceptor]
        ... )
    """

    pricing: dict[str, dict[str, dict[str, float]]] = field(default_factory=lambda: DEFAULT_PRICING)
    on_cost: Callable[[float, dict[str, int]], None] | None = None
    total_cost: float = field(default=0.0, init=False)
    request_count: int = field(default=0, init=False)

    def _calculate_cost(
        self, provider: str, model: str, input_tokens: int, output_tokens: int
    ) -> float:
        """Calculate cost for a request.

        Args:
            provider: Provider name
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in USD
        """
        provider_pricing = self.pricing.get(provider, {})
        model_pricing = provider_pricing.get(model, {})

        input_price = model_pricing.get("input", 0.0)
        output_price = model_pricing.get("output", 0.0)

        input_cost = (input_tokens / 1_000_000) * input_price
        output_cost = (output_tokens / 1_000_000) * output_price

        return input_cost + output_cost

    async def leave(self, ctx: Context) -> Context:
        """Track costs after successful response."""
        if ctx.response:
            model_info = ctx.model.model_info()
            provider = model_info.provider
            model = model_info.model

            input_tokens = ctx.response.usage.input_tokens
            output_tokens = ctx.response.usage.output_tokens

            cost = self._calculate_cost(provider, model, input_tokens, output_tokens)

            self.total_cost += cost
            self.request_count += 1

            token_info = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": ctx.response.usage.total_tokens or (input_tokens + output_tokens),
            }

            if self.on_cost:
                self.on_cost(cost, token_info)

            ctx.metadata["cost"] = cost
            ctx.metadata["total_cost"] = self.total_cost
            ctx.metadata["request_count"] = self.request_count

        return ctx
