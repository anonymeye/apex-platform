"""Evaluation run and score models."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apex.models.base import BaseModel


class SavedConversation(BaseModel):
    """Saved conversation bookmark for evaluation (references Redis state by user_id + conversation_id)."""

    __tablename__ = "saved_conversations"

    organization_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), nullable=False, index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), nullable=False
    )
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    agent_id: Mapped[Optional[UUID]] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    __table_args__ = (Index("ix_saved_conversations_created_at", "created_at"),)


class EvaluationJudgeConfig(BaseModel):
    """Reusable judge configuration (prompt template, rubric, model)."""

    __tablename__ = "evaluation_judge_configs"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    prompt_template: Mapped[str] = mapped_column(Text, nullable=False)
    rubric: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    model_ref_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("model_refs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )


class EvaluationRun(BaseModel):
    """One evaluation run: scope (what to evaluate) + judge config snapshot + status."""

    __tablename__ = "evaluation_runs"

    scope_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # e.g. "single" | "batch"
    scope_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    judge_config_snapshot: Mapped[dict] = mapped_column(
        JSON, nullable=False
    )  # prompt_template, rubric, model_ref_id at run time
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending", index=True
    )  # pending | running | completed | failed
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    organization_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_id: Mapped[Optional[UUID]] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    judge_config_id: Mapped[Optional[UUID]] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("evaluation_judge_configs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    scores: Mapped[list["EvaluationScore"]] = relationship(
        "EvaluationScore",
        back_populates="run",
        cascade="all, delete-orphan",
    )

    __table_args__ = (Index("ix_evaluation_runs_created_at", "created_at"),)


class EvaluationScore(BaseModel):
    """One scored item within a run (one conversation turn or test case)."""

    __tablename__ = "evaluation_scores"

    run_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("evaluation_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), nullable=False, index=True
    )
    turn_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    scores: Mapped[dict] = mapped_column(JSON, nullable=False)  # e.g. {"accuracy": 4, "tone": 5}
    raw_judge_output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    human_score: Mapped[Optional[float]] = mapped_column(nullable=True)
    human_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    human_reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    run: Mapped["EvaluationRun"] = relationship(
        "EvaluationRun",
        back_populates="scores",
    )

    __table_args__ = (
        Index("ix_evaluation_scores_run_conversation", "run_id", "conversation_id", "turn_index"),
    )
