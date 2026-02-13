"""Resolve a single turn (user message + agent response) or full transcript from conversation messages."""

from __future__ import annotations

import json
from typing import Any

from apex.ml.evaluation.judge import TurnInput


def _content_to_str(content: Any) -> str:
    """Normalize message content to a string for display."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            (b.get("text", "") if isinstance(b, dict) else str(b) for b in content
        ))
    return str(content) if content else ""


def messages_to_full_transcript(messages: list[dict[str, Any]]) -> str:
    """Format all messages as a single transcript for whole-conversation evaluation.

    Args:
        messages: List of message dicts (e.g. from ConversationState.messages).

    Returns:
        A single string with "User:", "Assistant:", "Tool:" lines.
    """
    if not messages:
        return "(empty conversation)"
    parts: list[str] = []
    for m in messages:
        role = (m.get("role") or "unknown").lower()
        content = m.get("content", "")
        text = _content_to_str(content)
        if role == "user":
            parts.append(f"User:\n{text}")
        elif role == "assistant":
            tool_calls = m.get("tool_calls")
            if isinstance(tool_calls, list) and tool_calls:
                tc_summary = "; ".join(
                    tc.get("function", {}).get("name", "?") if isinstance(tc, dict) else "?"
                    for tc in tool_calls
                )
                parts.append(f"Assistant: [tool calls: {tc_summary}]\n{text}")
            else:
                parts.append(f"Assistant:\n{text}")
        elif role == "tool":
            parts.append(f"Tool result:\n{text[:500]}{'...' if len(text) > 500 else ''}")
        else:
            parts.append(f"{role.capitalize()}:\n{text}")
    return "\n\n---\n\n".join(parts)


def messages_to_turn_input(messages: list[dict[str, Any]], turn_index: int) -> TurnInput | None:
    """Extract the Nth turn (0-based) from a list of stored messages.

    A turn is one user message followed by the assistant response (and any
    tool/tool_result messages before the next user message). Messages are
    expected in stored format: {"role": "user"|"assistant"|"tool", "content": ..., "tool_calls": ...}.

    Args:
        messages: List of message dicts (e.g. from ConversationState.messages).
        turn_index: 0-based turn index (0 = first user+assistant pair).

    Returns:
        TurnInput for that turn, or None if turn_index is out of range or turn is incomplete.
    """
    if not messages or turn_index < 0:
        return None
    user_indices = [i for i, m in enumerate(messages) if (m.get("role") or "").lower() == "user"]
    if turn_index >= len(user_indices):
        return None
    start = user_indices[turn_index]
    end = user_indices[turn_index + 1] if turn_index + 1 < len(user_indices) else len(messages)

    user_message = ""
    if messages[start].get("role", "").lower() == "user":
        content = messages[start].get("content", "")
        user_message = content if isinstance(content, str) else json.dumps(content)

    # Collect assistant content and tool_calls from this block (user start -> next user or end)
    agent_parts: list[str] = []
    tool_calls_summary_parts: list[str] = []
    for i in range(start + 1, end):
        m = messages[i]
        role = (m.get("role") or "").lower()
        content = m.get("content", "")
        if isinstance(content, list):
            content = " ".join(
                (b.get("text", "") if isinstance(b, dict) else str(b) for b in content)
            )
        elif not isinstance(content, str):
            content = str(content) if content else ""
        if role == "assistant":
            if content:
                agent_parts.append(content)
            tool_calls = m.get("tool_calls")
            if isinstance(tool_calls, list) and tool_calls:
                for tc in tool_calls:
                    name = tc.get("function", {}).get("name", "?") if isinstance(tc, dict) else "?"
                    args_raw = tc.get("function", {}).get("arguments", "") if isinstance(tc, dict) else ""
                    args_str = args_raw if isinstance(args_raw, str) else json.dumps(args_raw)
                    tool_calls_summary_parts.append(f"- {name}: {args_str[:200]}{'...' if len(args_str) > 200 else ''}")
        elif role == "tool":
            if content:
                agent_parts.append(f"[Tool result: {content[:300]}{'...' if len(content) > 300 else ''}]")

    agent_response = "\n".join(agent_parts) if agent_parts else ""
    tool_calls_summary = "\n".join(tool_calls_summary_parts) if tool_calls_summary_parts else None
    return TurnInput(
        user_message=user_message or "(empty)",
        agent_response=agent_response or "(no response)",
        tool_calls_summary=tool_calls_summary,
    )
