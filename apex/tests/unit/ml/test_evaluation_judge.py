"""Unit tests for LLM judge (evaluation)."""

import os

import pytest

from apex.ml.evaluation.judge import (
    DEFAULT_JUDGE_PROMPT_TEMPLATE,
    JudgeConfig,
    JudgeResult,
    TurnInput,
    _build_prompt,
    _parse_judge_response,
    run_judge,
)


def test_parse_judge_response_valid_json():
    raw = '{"scores": {"accuracy": 4, "helpfulness": 5}, "comment": "Good."}'
    result = _parse_judge_response(raw)
    assert result.scores == {"accuracy": 4.0, "helpfulness": 5.0}
    assert result.comment == "Good."
    assert result.raw_output == raw


def test_parse_judge_response_json_in_code_block():
    raw = 'Here is the result:\n```json\n{"scores": {"tone": 3}, "comment": null}\n```'
    result = _parse_judge_response(raw)
    assert result.scores == {"tone": 3.0}
    assert result.comment is None


def test_parse_judge_response_invalid_json_returns_empty_scores():
    raw = "Not JSON at all."
    result = _parse_judge_response(raw)
    assert result.scores == {}
    assert result.raw_output == raw
    assert result.comment is None


def test_build_prompt_replaces_placeholders():
    turn = TurnInput(
        user_message="What is 2+2?",
        agent_response="4",
        tool_calls_summary=None,
    )
    rubric = {"accuracy": "1-5", "helpfulness": "1-5"}
    prompt = _build_prompt(DEFAULT_JUDGE_PROMPT_TEMPLATE, turn, rubric)
    assert "What is 2+2?" in prompt
    assert "4" in prompt
    assert "accuracy" in prompt
    assert "(none)" in prompt


def test_judge_config_from_snapshot():
    snapshot = {
        "model": "gpt-4o-mini",
        "provider": "openai",
        "rubric": {"accuracy": "1-5"},
    }
    config = JudgeConfig.from_snapshot(snapshot)
    assert config.model == "gpt-4o-mini"
    assert config.provider == "openai"
    assert config.rubric == {"accuracy": "1-5"}
    assert config.prompt_template == DEFAULT_JUDGE_PROMPT_TEMPLATE


def test_judge_config_from_settings():
    config = JudgeConfig.from_settings()
    assert config.model
    assert config.provider in ("openai", "anthropic", "groq")
    assert config.prompt_template == DEFAULT_JUDGE_PROMPT_TEMPLATE


@pytest.mark.asyncio
async def test_run_judge_with_groq():
    """Call the real judge using Groq (skipped if GROQ_API_KEY not set)."""
    if not os.getenv("GROQ_API_KEY"):
        pytest.skip("GROQ_API_KEY not set; use Groq for judge tests without OpenAI")
    turn = TurnInput(
        user_message="What is 2 + 2?",
        agent_response="2 + 2 equals 4.",
        tool_calls_summary=None,
    )
    config = JudgeConfig(
        model="llama-3.1-8b-instant",
        provider="groq",
        prompt_template=DEFAULT_JUDGE_PROMPT_TEMPLATE,
        rubric={"accuracy": "1-5", "helpfulness": "1-5"},
        api_key_env_var="GROQ_API_KEY",
        base_url=None,
    )
    result = await run_judge(turn, config)
    assert isinstance(result, JudgeResult)
    assert isinstance(result.scores, dict)
    assert result.raw_output
    # Groq may return scores with different dimension names; at least one score expected
    assert len(result.scores) >= 1
    for _k, v in result.scores.items():
        assert isinstance(v, (int, float))
        assert 0 <= v <= 5
