"""LLM-as-judge: score a single turn (user message + agent response) with no storage."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any

from conduit.providers.anthropic import AnthropicModel
from conduit.providers.groq import GroqModel
from conduit.providers.openai import OpenAIModel
from conduit.schema.messages import Message
from conduit.schema.options import ChatOptions

logger = logging.getLogger(__name__)

# Default prompt template; placeholders: {{ user_message }}, {{ agent_response }}, {{ rubric }}, {{ tool_calls }}
DEFAULT_JUDGE_PROMPT_TEMPLATE = """You are an expert evaluator. Score the agent's response to the user on the given dimensions.

User message:
{{ user_message }}

Agent response:
{{ agent_response }}

Tool calls (if any):
{{ tool_calls }}

Rubric / dimensions to score (1-5, 1=poor, 5=excellent):
{{ rubric }}

Respond with a single JSON object only, no other text. Example:
{"scores": {"accuracy": 4, "helpfulness": 5, "tone": 4}, "comment": "Brief optional comment"}
"""


@dataclass
class TurnInput:
    """One turn to evaluate: user message + agent response."""

    user_message: str
    agent_response: str
    tool_calls_summary: str | None = None


@dataclass
class JudgeResult:
    """Result of running the LLM judge on one turn. Caller persists; this module does not."""

    scores: dict[str, float | int]
    raw_output: str
    comment: str | None = None


@dataclass
class JudgeConfig:
    """Judge run-time config: model, provider, prompt template, rubric. From snapshot or settings."""

    model: str
    provider: str
    prompt_template: str
    rubric: dict[str, Any] | None = None
    api_key_env_var: str | None = None
    base_url: str | None = None

    @classmethod
    def from_snapshot(cls, snapshot: dict[str, Any]) -> "JudgeConfig":
        """Build JudgeConfig from a run's judge_config_snapshot (and optional defaults)."""
        return cls(
            model=snapshot.get("model", "gpt-4o-mini"),
            provider=(snapshot.get("provider") or "openai").lower(),
            prompt_template=snapshot.get("prompt_template") or DEFAULT_JUDGE_PROMPT_TEMPLATE,
            rubric=snapshot.get("rubric"),
            api_key_env_var=snapshot.get("api_key_env_var"),
            base_url=snapshot.get("base_url"),
        )

    @classmethod
    def from_settings(cls) -> "JudgeConfig":
        """Build JudgeConfig from application settings (default judge)."""
        from apex.core.config import settings

        return cls(
            model=settings.judge_model,
            provider=settings.judge_provider.lower(),
            prompt_template=DEFAULT_JUDGE_PROMPT_TEMPLATE,
            rubric=None,
            api_key_env_var=settings.judge_api_key_env_var,
            base_url=None,
        )


def _resolve_judge_api_key(provider: str, api_key_env_var: str | None) -> str | None:
    """Resolve API key from env. Returns None if provider uses no key."""
    provider = (provider or "openai").lower()
    env_var = api_key_env_var or {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "groq": "GROQ_API_KEY",
    }.get(provider, "OPENAI_API_KEY")
    return os.getenv(env_var)


def _create_judge_model(config: JudgeConfig) -> OpenAIModel | AnthropicModel | GroqModel:
    """Create a Conduit chat model for the judge from JudgeConfig."""
    api_key = _resolve_judge_api_key(config.provider, config.api_key_env_var)
    provider = (config.provider or "openai").lower()
    model_id = config.model or "gpt-4o-mini"
    base_url = config.base_url or ""

    if provider == "openai":
        if not api_key and not base_url:
            raise ValueError(
                "OPENAI_API_KEY (or judge_api_key_env_var) must be set for OpenAI judge"
            )
        return OpenAIModel(
            api_key=api_key,
            model=model_id,
            base_url=base_url or "https://api.openai.com/v1",
        )
    if provider == "anthropic":
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY (or judge_api_key_env_var) must be set for Anthropic judge"
            )
        return AnthropicModel(
            api_key=api_key,
            model=model_id,
            base_url=base_url or "https://api.anthropic.com/v1",
        )
    if provider == "groq":
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY (or judge_api_key_env_var) must be set for Groq judge"
            )
        return GroqModel(
            api_key=api_key,
            model=model_id,
            base_url=base_url or "https://api.groq.com/openai/v1",
        )
    raise ValueError(f"Unsupported judge provider: {config.provider}")


def _build_prompt(template: str, turn: TurnInput, rubric: dict[str, Any] | None) -> str:
    """Fill the judge prompt template with turn data and rubric."""
    rubric_str = json.dumps(rubric, indent=2) if rubric else "accuracy, helpfulness, tone (1-5 each)"
    prompt = (
        template.replace("{{ user_message }}", turn.user_message)
        .replace("{{ agent_response }}", turn.agent_response)
        .replace("{{ rubric }}", rubric_str)
        .replace("{{ tool_calls }}", turn.tool_calls_summary or "(none)")
    )
    return prompt


def _parse_judge_response(content: str) -> JudgeResult:
    """Parse judge LLM response into scores and optional comment. Tolerates markdown code blocks."""
    raw = (content or "").strip()
    # Try to extract JSON from markdown code block if present
    if "```json" in raw:
        start = raw.find("```json") + 7
        end = raw.find("```", start)
        raw = raw[start:end].strip() if end > start else raw
    elif "```" in raw:
        start = raw.find("```") + 3
        end = raw.find("```", start)
        raw = raw[start:end].strip() if end > start else raw
    try:
        data = json.loads(raw)
        scores = data.get("scores")
        if not isinstance(scores, dict):
            scores = {}
        # Normalize to numbers
        scores = {k: (float(v) if isinstance(v, (int, float)) else 0) for k, v in scores.items()}
        comment = data.get("comment")
        if comment is not None:
            comment = str(comment).strip() or None
        return JudgeResult(scores=scores, raw_output=content, comment=comment)
    except json.JSONDecodeError as e:
        logger.warning("Judge response was not valid JSON: %s", e)
        return JudgeResult(scores={}, raw_output=content, comment=None)


async def run_judge(turn: TurnInput, config: JudgeConfig) -> JudgeResult:
    """Run the LLM judge on one turn. No DB; caller persists.

    Args:
        turn: User message + agent response (and optional tool calls summary).
        config: Judge model, provider, prompt template, rubric.

    Returns:
        JudgeResult with scores dict, raw_output, and optional comment.

    Raises:
        ValueError: If judge provider/config or API key is invalid.
    """
    model = _create_judge_model(config)
    prompt = _build_prompt(config.prompt_template, turn, config.rubric)
    messages = [Message(role="user", content=prompt)]
    opts = ChatOptions(temperature=0.0, max_tokens=1024)
    async with model:
        response = await model.chat(messages, opts)
    content = response.extract_content()
    return _parse_judge_response(content)
