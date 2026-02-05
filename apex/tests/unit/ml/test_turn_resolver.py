"""Unit tests for turn resolver (messages -> TurnInput)."""

import pytest

from apex.ml.evaluation.turn_resolver import messages_to_turn_input


def test_empty_messages_returns_none():
    assert messages_to_turn_input([], 0) is None
    assert messages_to_turn_input([], 1) is None


def test_negative_turn_index_returns_none():
    assert messages_to_turn_input([{"role": "user", "content": "Hi"}], -1) is None


def test_single_turn_user_and_assistant():
    messages = [
        {"role": "user", "content": "What is 2+2?"},
        {"role": "assistant", "content": "2+2 equals 4."},
    ]
    turn = messages_to_turn_input(messages, 0)
    assert turn is not None
    assert turn.user_message == "What is 2+2?"
    assert turn.agent_response == "2+2 equals 4."
    assert turn.tool_calls_summary is None


def test_second_turn():
    messages = [
        {"role": "user", "content": "First?"},
        {"role": "assistant", "content": "First answer."},
        {"role": "user", "content": "Second?"},
        {"role": "assistant", "content": "Second answer."},
    ]
    turn0 = messages_to_turn_input(messages, 0)
    turn1 = messages_to_turn_input(messages, 1)
    assert turn0 is not None
    assert turn0.user_message == "First?"
    assert turn0.agent_response == "First answer."
    assert turn1 is not None
    assert turn1.user_message == "Second?"
    assert turn1.agent_response == "Second answer."


def test_turn_index_out_of_range_returns_none():
    messages = [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello."},
    ]
    assert messages_to_turn_input(messages, 1) is None
    assert messages_to_turn_input(messages, 2) is None


def test_tool_calls_summarized():
    messages = [
        {"role": "user", "content": "Search for X"},
        {
            "role": "assistant",
            "content": "I'll search.",
            "tool_calls": [
                {"function": {"name": "search", "arguments": '{"q": "X"}'}},
            ],
        },
    ]
    turn = messages_to_turn_input(messages, 0)
    assert turn is not None
    assert "search" in (turn.tool_calls_summary or "")
    assert "X" in (turn.tool_calls_summary or "")


def test_tool_result_appended_to_agent_response():
    messages = [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Calling tool..."},
        {"role": "tool", "content": "Tool result here."},
    ]
    turn = messages_to_turn_input(messages, 0)
    assert turn is not None
    assert "Calling tool" in turn.agent_response
    assert "Tool result" in turn.agent_response


def test_empty_user_message_normalized():
    messages = [
        {"role": "user", "content": ""},
        {"role": "assistant", "content": "Hi there."},
    ]
    turn = messages_to_turn_input(messages, 0)
    assert turn is not None
    assert turn.user_message == "(empty)"
    assert turn.agent_response == "Hi there."


def test_no_assistant_response_normalized():
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "tool", "content": "Only tool, no assistant text."},
    ]
    turn = messages_to_turn_input(messages, 0)
    assert turn is not None
    assert turn.user_message == "Hello"
    assert "(no response)" in turn.agent_response or "tool" in turn.agent_response.lower()
