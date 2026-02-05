"""Evaluation service: orchestrate runs, load turns (Redis/inline), call judge, persist scores."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from apex.ml.evaluation.judge import JudgeConfig, JudgeResult, TurnInput, run_judge
from apex.ml.evaluation.turn_resolver import messages_to_turn_input
from apex.models.evaluation import EvaluationRun, EvaluationScore
from apex.repositories.evaluation_repository import (
    EvaluationRunRepository,
    EvaluationScoreRepository,
)
from apex.storage.conversation_state_store import ConversationStateStore

logger = logging.getLogger(__name__)


@dataclass
class ScopeItem:
    """One item to evaluate in a run: conversation + turn + turn input."""

    conversation_id: UUID
    turn_index: int
    turn: TurnInput


# Scope payload formats (see IMPLEMENTATION_PLAN Phase 1.4):
# - single + ref: {"conversation_id": "...", "user_id": "...", "turn_index": 0}
# - single + inline: {"inline": {"user_message": "...", "agent_response": "...", "tool_calls_summary": null}, "conversation_id": "..."}
# - batch: {"items": [{"conversation_id": "...", "user_id": "...", "turn_index": 0} | {"conversation_id": "...", "inline": {...}}, ...]}


class EvaluationService:
    """Orchestrates evaluation runs: create run, resolve scope, run judge, persist scores."""

    def __init__(
        self,
        run_repo: EvaluationRunRepository,
        score_repo: EvaluationScoreRepository,
        conversation_state_store: ConversationStateStore | None = None,
    ):
        self.run_repo = run_repo
        self.score_repo = score_repo
        self.conversation_state_store = conversation_state_store

    async def create_run(
        self,
        scope_type: str,
        scope_payload: dict[str, Any],
        judge_config_snapshot: dict[str, Any],
        organization_id: UUID,
        agent_id: UUID | None = None,
        judge_config_id: UUID | None = None,
    ) -> EvaluationRun:
        """Create an evaluation run (status=pending). Caller must commit the session."""
        run = await self.run_repo.create(
            scope_type=scope_type,
            scope_payload=scope_payload,
            judge_config_snapshot=judge_config_snapshot,
            status="pending",
            organization_id=organization_id,
            agent_id=agent_id,
            judge_config_id=judge_config_id,
        )
        logger.info("Created evaluation run %s (scope_type=%s)", run.id, scope_type)
        return run

    async def get_scope_items(
        self,
        scope_type: str,
        scope_payload: dict[str, Any],
    ) -> list[ScopeItem]:
        """Resolve scope to a list of (conversation_id, turn_index, TurnInput). Loads from Redis when refs are used."""
        items: list[ScopeItem] = []
        if scope_type == "single":
            one = self._resolve_single_item(scope_payload)
            if one is not None:
                items.append(one)
        elif scope_type == "batch":
            batch_list = scope_payload.get("items") or []
            for raw in batch_list:
                if not isinstance(raw, dict):
                    continue
                one = await self._resolve_batch_item(raw)
                if one is not None:
                    items.append(one)
        return items

    def _resolve_single_item(self, payload: dict[str, Any]) -> ScopeItem | None:
        """Resolve a single scope payload (sync: inline only; ref needs async)."""
        inline = payload.get("inline")
        if isinstance(inline, dict):
            conv_id = payload.get("conversation_id")
            if not conv_id:
                return None
            try:
                cid = UUID(conv_id) if isinstance(conv_id, str) else conv_id
            except (TypeError, ValueError):
                return None
            turn = TurnInput(
                user_message=str(inline.get("user_message", "")),
                agent_response=str(inline.get("agent_response", "")),
                tool_calls_summary=inline.get("tool_calls_summary"),
            )
            return ScopeItem(conversation_id=cid, turn_index=0, turn=turn)
        # Ref form: need async load; cannot resolve here
        return None

    async def _resolve_batch_item(self, raw: dict[str, Any]) -> ScopeItem | None:
        """Resolve one batch item: either inline or ref (load from Redis)."""
        inline = raw.get("inline")
        conv_id = raw.get("conversation_id")
        if not conv_id:
            return None
        try:
            cid = UUID(conv_id) if isinstance(conv_id, str) else conv_id
        except (TypeError, ValueError):
            return None
        if isinstance(inline, dict):
            turn = TurnInput(
                user_message=str(inline.get("user_message", "")),
                agent_response=str(inline.get("agent_response", "")),
                tool_calls_summary=inline.get("tool_calls_summary"),
            )
            turn_index = int(raw.get("turn_index", 0))
            return ScopeItem(conversation_id=cid, turn_index=turn_index, turn=turn)
        # Ref: conversation_id + user_id + turn_index
        user_id_raw = raw.get("user_id")
        turn_index = int(raw.get("turn_index", 0))
        if not user_id_raw or not self.conversation_state_store:
            return None
        try:
            uid = UUID(user_id_raw) if isinstance(user_id_raw, str) else user_id_raw
        except (TypeError, ValueError):
            return None
        state = await self.conversation_state_store.get(uid, cid)
        if not state or not state.messages:
            return None
        turn_input = messages_to_turn_input(state.messages, turn_index)
        if turn_input is None:
            return None
        return ScopeItem(conversation_id=cid, turn_index=turn_index, turn=turn_input)

    async def resolve_scope_items(
        self,
        scope_type: str,
        scope_payload: dict[str, Any],
    ) -> list[ScopeItem]:
        """Resolve full scope to scope items. For single+ref we need to load from Redis here."""
        if scope_type == "single":
            inline = scope_payload.get("inline")
            if isinstance(inline, dict):
                return self.get_scope_items(scope_type, scope_payload)
            # Single ref
            conv_id = scope_payload.get("conversation_id")
            user_id_raw = scope_payload.get("user_id")
            turn_index = int(scope_payload.get("turn_index", 0))
            if not conv_id or not user_id_raw or not self.conversation_state_store:
                return []
            try:
                cid = UUID(conv_id) if isinstance(conv_id, str) else conv_id
                uid = UUID(user_id_raw) if isinstance(user_id_raw, str) else user_id_raw
            except (TypeError, ValueError):
                return []
            state = await self.conversation_state_store.get(uid, cid)
            if not state or not state.messages:
                return []
            turn_input = messages_to_turn_input(state.messages, turn_index)
            if turn_input is None:
                return []
            return [ScopeItem(conversation_id=cid, turn_index=turn_index, turn=turn_input)]
        return await self.get_scope_items(scope_type, scope_payload)

    async def execute_run(self, run_id: UUID) -> None:
        """
        Load run, resolve scope items, run judge for each, persist scores, update run status.
        Caller must commit the session after this returns.
        """
        run = await self.run_repo.get_with_scores(run_id)
        if not run:
            logger.warning("Evaluation run %s not found", run_id)
            return
        if run.status != "pending":
            logger.info("Evaluation run %s already in status %s, skipping", run_id, run.status)
            return

        await self.run_repo.update(run_id, status="running")
        config = JudgeConfig.from_snapshot(run.judge_config_snapshot)
        scope_items = await self.resolve_scope_items(run.scope_type, run.scope_payload)
        if not scope_items:
            await self.run_repo.update(
                run_id, status="completed", error_message="No items to evaluate"
            )
            logger.warning("Evaluation run %s had no scope items", run_id)
            return
        first_error: str | None = None
        for item in scope_items:
            try:
                result: JudgeResult = await run_judge(item.turn, config)
                await self.score_repo.create(
                    run_id=run_id,
                    conversation_id=item.conversation_id,
                    turn_index=item.turn_index,
                    scores=result.scores,
                    raw_judge_output=result.raw_output,
                )
            except Exception as e:
                err_msg = f"{type(e).__name__}: {e}"
                logger.exception("Judge failed for run %s conversation %s turn %s", run_id, item.conversation_id, item.turn_index)
                if first_error is None:
                    first_error = err_msg
                # Continue with other items; we still persist run as completed with error_message
        await self.run_repo.update(
            run_id,
            status="completed",
            error_message=first_error,
        )
        logger.info(
            "Evaluation run %s finished (scores=%d, error=%s)",
            run_id,
            len(scope_items),
            first_error or "none",
        )
