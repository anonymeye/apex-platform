"""Evaluation run and score API endpoints (Phase 1.7)."""

from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from apex.api.dependencies import get_current_user_from_token
from apex.api.v1.schemas.evaluation import (
    CreateRunRequest,
    CreateRunResponse,
    InlineJudgeConfig,
    ListRunsResponse,
    ListScoresResponse,
    RunDetailResponse,
    RunListItem,
    ScoreResponse,
)
from apex.core.config import settings
from apex.core.database import get_db
from apex.ml.evaluation.judge import JudgeConfig
from apex.queue import enqueue_evaluation_run
from apex.repositories.evaluation_repository import (
    EvaluationJudgeConfigRepository,
    EvaluationRunRepository,
    EvaluationScoreRepository,
)
from apex.repositories.model_ref_repository import ModelRefRepository
from apex.services.evaluation_service import EvaluationService
from apex.storage.conversation_state_store import ConversationStateStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


def _build_judge_snapshot_from_model_ref(model_ref) -> dict:
    """Build judge_config_snapshot dict from a ModelRef (with connection loaded)."""
    conn = model_ref.connection
    return {
        "model": model_ref.runtime_id,
        "provider": (conn.provider or "openai").lower(),
        "prompt_template": None,  # caller must set
        "rubric": None,
        "api_key_env_var": conn.api_key_env_var,
        "base_url": conn.base_url,
    }


async def _resolve_judge_config_snapshot(
    db: AsyncSession,
    organization_id: UUID,
    judge_config_id: UUID | None,
    inline_judge_config: InlineJudgeConfig | None,
) -> dict:
    """
    Resolve request to a judge_config_snapshot dict for storage on the run.
    Exactly one of judge_config_id or inline_judge_config should be used; if both omitted, use app default.
    """
    if judge_config_id is not None and inline_judge_config is not None:
        raise ValueError("Provide either judge_config_id or inline_judge_config, not both")

    if judge_config_id is not None:
        judge_repo = EvaluationJudgeConfigRepository(db)
        model_ref_repo = ModelRefRepository(db)
        config = await judge_repo.get_by_id_and_organization(judge_config_id, organization_id)
        if not config:
            raise ValueError(f"Judge config {judge_config_id} not found")
        model_ref = await model_ref_repo.get_for_org(config.model_ref_id, organization_id)
        if not model_ref or not model_ref.connection:
            raise ValueError("Judge config model ref or connection not found")
        snapshot = _build_judge_snapshot_from_model_ref(model_ref)
        snapshot["prompt_template"] = config.prompt_template
        snapshot["rubric"] = config.rubric
        return snapshot

    # Inline or default
    default_cfg = JudgeConfig.from_settings()
    if inline_judge_config is not None and inline_judge_config.model_ref_id is not None:
        model_ref_repo = ModelRefRepository(db)
        model_ref = await model_ref_repo.get_for_org(
            inline_judge_config.model_ref_id, organization_id
        )
        if not model_ref or not model_ref.connection:
            raise ValueError("Inline model_ref_id not found")
        snapshot = _build_judge_snapshot_from_model_ref(model_ref)
    else:
        snapshot = {
            "model": default_cfg.model,
            "provider": default_cfg.provider,
            "prompt_template": default_cfg.prompt_template,
            "rubric": default_cfg.rubric,
            "api_key_env_var": default_cfg.api_key_env_var,
            "base_url": default_cfg.base_url,
        }
    if inline_judge_config is not None:
        if inline_judge_config.prompt_template is not None:
            snapshot["prompt_template"] = inline_judge_config.prompt_template
        if inline_judge_config.rubric is not None:
            snapshot["rubric"] = inline_judge_config.rubric
    if not snapshot.get("prompt_template"):
        snapshot["prompt_template"] = default_cfg.prompt_template
    return snapshot


@router.post("/runs", response_model=CreateRunResponse, status_code=status.HTTP_201_CREATED)
async def create_evaluation_run(
    body: CreateRunRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_current_user_from_token),
):
    """
    Create an evaluation run, enqueue it for the worker, and return run_id.
    Body: scope_type, scope_payload, and either judge_config_id or inline_judge_config (or neither for app default).
    """
    organization_id = UUID(user_data["org_id"])
    if body.scope_type not in ("single", "batch"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="scope_type must be 'single' or 'batch'",
        )
    try:
        judge_snapshot = await _resolve_judge_config_snapshot(
            db, organization_id, body.judge_config_id, body.inline_judge_config
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    run_repo = EvaluationRunRepository(db)
    score_repo = EvaluationScoreRepository(db)
    redis = getattr(request.app.state, "redis", None)
    if not redis:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis unavailable; cannot enqueue evaluation jobs",
        )
    store = ConversationStateStore(
        redis,
        ttl_seconds=settings.conversation_state_ttl_seconds,
    )
    svc = EvaluationService(
        run_repo=run_repo,
        score_repo=score_repo,
        conversation_state_store=store,
    )
    run = await svc.create_run(
        scope_type=body.scope_type,
        scope_payload=body.scope_payload,
        judge_config_snapshot=judge_snapshot,
        organization_id=organization_id,
        agent_id=body.agent_id,
        judge_config_id=body.judge_config_id,
    )
    await enqueue_evaluation_run(redis, run.id)
    return CreateRunResponse(run_id=run.id)


@router.get("/runs/{run_id}", response_model=RunDetailResponse)
async def get_evaluation_run(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_current_user_from_token),
):
    """Get run status and summary (e.g. score count)."""
    organization_id = UUID(user_data["org_id"])
    run_repo = EvaluationRunRepository(db)
    score_repo = EvaluationScoreRepository(db)
    run = await run_repo.get(run_id)
    if not run or run.organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation run not found",
        )
    score_count = await score_repo.count_by_run_id(run_id)
    return RunDetailResponse(
        id=run.id,
        scope_type=run.scope_type,
        status=run.status,
        score_count=score_count,
        error_message=run.error_message,
        organization_id=run.organization_id,
        agent_id=run.agent_id,
        judge_config_id=run.judge_config_id,
        created_at=run.created_at.isoformat(),
        updated_at=run.updated_at.isoformat(),
    )


@router.get("/runs/{run_id}/scores", response_model=ListScoresResponse)
async def list_evaluation_scores(
    run_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_current_user_from_token),
):
    """List scores for a run (paginated)."""
    organization_id = UUID(user_data["org_id"])
    run_repo = EvaluationRunRepository(db)
    score_repo = EvaluationScoreRepository(db)
    run = await run_repo.get(run_id)
    if not run or run.organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation run not found",
        )
    total = await score_repo.count_by_run_id(run_id)
    scores = await score_repo.list_by_run_id(run_id, skip=skip, limit=limit)
    return ListScoresResponse(
        run_id=run_id,
        items=[
            ScoreResponse(
                id=s.id,
                run_id=s.run_id,
                conversation_id=s.conversation_id,
                turn_index=s.turn_index,
                scores=s.scores,
                raw_judge_output=s.raw_judge_output,
                human_score=s.human_score,
                human_comment=s.human_comment,
                created_at=s.created_at.isoformat(),
            )
            for s in scores
        ],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/runs", response_model=ListRunsResponse)
async def list_evaluation_runs(
    run_status: str | None = Query(None, alias="status", description="Filter by run status"),
    created_after: datetime | None = None,
    created_before: datetime | None = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_current_user_from_token),
):
    """List evaluation runs (filter by time, status)."""
    organization_id = UUID(user_data["org_id"])
    run_repo = EvaluationRunRepository(db)
    score_repo = EvaluationScoreRepository(db)
    runs = await run_repo.list_by_organization(
        organization_id=organization_id,
        status=run_status,
        created_after=created_after,
        created_before=created_before,
        skip=skip,
        limit=limit,
    )
    total = await run_repo.count_by_organization(
        organization_id=organization_id,
        status=run_status,
        created_after=created_after,
        created_before=created_before,
    )
    items = []
    for run in runs:
        count = await score_repo.count_by_run_id(run.id)
        items.append(
            RunListItem(
                id=run.id,
                scope_type=run.scope_type,
                status=run.status,
                score_count=count,
                error_message=run.error_message,
                created_at=run.created_at.isoformat(),
                updated_at=run.updated_at.isoformat(),
            )
        )
    return ListRunsResponse(items=items, total=total, skip=skip, limit=limit)
