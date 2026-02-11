"""Evaluation run and score API schemas."""

from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


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
        description="Model reference for judge LLM; if omitted, app default judge model is used",
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
