"""Evaluation run and score API schemas."""

from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# --- Judge config (stored configs for evaluation judge) ---


class JudgeConfigCreate(BaseModel):
    """Request body for POST /evaluation/judge-configs."""

    name: str = Field(..., min_length=1, max_length=255, description="Display name for this judge config")
    prompt_template: str = Field(
        ...,
        description="Judge prompt template (placeholders: {{ user_message }}, {{ agent_response }}, {{ rubric }}, {{ tool_calls }})",
    )
    rubric: Optional[dict[str, Any]] = Field(
        None,
        description="Rubric/dimensions to score (e.g. {\"accuracy\": \"1-5\", \"tone\": \"1-5\"})",
    )
    model_ref_id: UUID = Field(
        ...,
        description="Model reference for the judge LLM (must belong to your organization)",
    )


class JudgeConfigUpdate(BaseModel):
    """Request body for PATCH /evaluation/judge-configs/{id}."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    prompt_template: Optional[str] = None
    rubric: Optional[dict[str, Any]] = None
    model_ref_id: Optional[UUID] = None


class JudgeConfigResponse(BaseModel):
    """Response for judge config get/list."""

    id: UUID
    name: str
    prompt_template: str
    rubric: Optional[dict[str, Any]] = None
    model_ref_id: UUID
    organization_id: UUID
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ListJudgeConfigsResponse(BaseModel):
    """Paginated list of judge configs."""

    items: list[JudgeConfigResponse]
    total: int
    skip: int
    limit: int


# --- Inline judge (for create run without stored config) ---


class InlineJudgeConfig(BaseModel):
    """Inline judge config when not using a stored judge_config_id."""

    prompt_template: Optional[str] = Field(
        None,
        description="Judge prompt template (placeholders: {{ user_message }}, {{ agent_response }}, {{ rubric }}, {{ tool_calls }})",
    )
    rubric: Optional[dict[str, Any]] = Field(
        None,
        description="Rubric/dimensions to score (e.g. {\"accuracy\": \"1-5\", \"tone\": \"1-5\"})",
    )
    model_ref_id: Optional[UUID] = Field(
        None,
        description="Model reference for judge LLM; required when using inline_judge_config",
    )


class CreateRunRequest(BaseModel):
    """Request body for POST /evaluation/runs."""

    scope_type: str = Field(
        ...,
        description="Scope type: 'single' or 'batch'",
    )
    scope_payload: dict[str, Any] = Field(
        ...,
        description="Scope payload. Single: { conversation_id, user_id?, turn_index?, inline? }. Batch: { items: [{ conversation_id, user_id?, turn_index?, inline? }, ...] }",
    )
    judge_config_id: Optional[UUID] = Field(
        None,
        description="ID of a stored evaluation judge config; mutually exclusive with inline_judge_config",
    )
    inline_judge_config: Optional[InlineJudgeConfig] = Field(
        None,
        description="Inline judge config when not using judge_config_id",
    )
    agent_id: Optional[UUID] = Field(
        None,
        description="Optional agent ID to associate with this run",
    )


class CreateRunResponse(BaseModel):
    """Response for POST /evaluation/runs."""

    run_id: UUID = Field(..., description="Created evaluation run ID")


class RunDetailResponse(BaseModel):
    """Run status and summary for GET /evaluation/runs/{run_id}."""

    id: UUID
    scope_type: str
    status: str = Field(..., description="pending | running | completed | failed")
    score_count: int = Field(..., description="Number of scores for this run")
    error_message: Optional[str] = None
    organization_id: UUID
    agent_id: Optional[UUID] = None
    judge_config_id: Optional[UUID] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class RunListItem(BaseModel):
    """Run summary for list endpoint."""

    id: UUID
    scope_type: str
    status: str
    score_count: int
    error_message: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class HumanScoreRequest(BaseModel):
    """Request body for POST /evaluation/runs/{run_id}/scores/{score_id}/human."""

    score: float = Field(..., description="Human-assigned score for this turn")
    comment: Optional[str] = Field(None, description="Optional comment from the reviewer")


class ScoreResponse(BaseModel):
    """One score for GET /evaluation/runs/{run_id}/scores."""

    id: UUID
    run_id: UUID
    conversation_id: UUID
    turn_index: int
    scores: dict[str, float | int] = Field(..., description="Dimension scores from judge")
    raw_judge_output: Optional[str] = None
    human_score: Optional[float] = None
    human_comment: Optional[str] = None
    human_reviewed_at: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class ListScoresResponse(BaseModel):
    """Paginated scores for a run."""

    run_id: UUID
    items: list[ScoreResponse]
    total: int
    skip: int
    limit: int


class ListRunsResponse(BaseModel):
    """Paginated list of runs."""

    items: list[RunListItem]
    total: int
    skip: int
    limit: int
