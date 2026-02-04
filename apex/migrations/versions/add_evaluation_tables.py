"""Add evaluation_runs, evaluation_scores, evaluation_judge_configs

Revision ID: add_evaluation_tables
Revises: add_vector_embeddings
Create Date: 2026-02-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "add_evaluation_tables"
down_revision: Union[str, None] = "add_vector_embeddings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "evaluation_judge_configs",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("prompt_template", sa.Text(), nullable=False),
        sa.Column("rubric", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("model_ref_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["model_ref_id"], ["model_refs.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_evaluation_judge_configs_model_ref_id"),
        "evaluation_judge_configs",
        ["model_ref_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_evaluation_judge_configs_organization_id"),
        "evaluation_judge_configs",
        ["organization_id"],
        unique=False,
    )

    op.create_table(
        "evaluation_runs",
        sa.Column("scope_type", sa.String(length=50), nullable=False),
        sa.Column(
            "scope_payload",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "judge_config_snapshot",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "judge_config_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["agent_id"], ["agents.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["judge_config_id"],
            ["evaluation_judge_configs.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_evaluation_runs_agent_id"),
        "evaluation_runs",
        ["agent_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_evaluation_runs_created_at"),
        "evaluation_runs",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_evaluation_runs_judge_config_id"),
        "evaluation_runs",
        ["judge_config_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_evaluation_runs_organization_id"),
        "evaluation_runs",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_evaluation_runs_status"),
        "evaluation_runs",
        ["status"],
        unique=False,
    )

    op.create_table(
        "evaluation_scores",
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("turn_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "scores",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("raw_judge_output", sa.Text(), nullable=True),
        sa.Column("human_score", sa.Float(), nullable=True),
        sa.Column("human_comment", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["run_id"], ["evaluation_runs.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_evaluation_scores_conversation_id"),
        "evaluation_scores",
        ["conversation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_evaluation_scores_run_conversation"),
        "evaluation_scores",
        ["run_id", "conversation_id", "turn_index"],
        unique=False,
    )
    op.create_index(
        op.f("ix_evaluation_scores_run_id"),
        "evaluation_scores",
        ["run_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_evaluation_scores_run_id"),
        table_name="evaluation_scores",
    )
    op.drop_index(
        op.f("ix_evaluation_scores_run_conversation"),
        table_name="evaluation_scores",
    )
    op.drop_index(
        op.f("ix_evaluation_scores_conversation_id"),
        table_name="evaluation_scores",
    )
    op.drop_table("evaluation_scores")

    op.drop_index(
        op.f("ix_evaluation_runs_status"),
        table_name="evaluation_runs",
    )
    op.drop_index(
        op.f("ix_evaluation_runs_organization_id"),
        table_name="evaluation_runs",
    )
    op.drop_index(
        op.f("ix_evaluation_runs_judge_config_id"),
        table_name="evaluation_runs",
    )
    op.drop_index(
        op.f("ix_evaluation_runs_created_at"),
        table_name="evaluation_runs",
    )
    op.drop_index(
        op.f("ix_evaluation_runs_agent_id"),
        table_name="evaluation_runs",
    )
    op.drop_table("evaluation_runs")

    op.drop_index(
        op.f("ix_evaluation_judge_configs_organization_id"),
        table_name="evaluation_judge_configs",
    )
    op.drop_index(
        op.f("ix_evaluation_judge_configs_model_ref_id"),
        table_name="evaluation_judge_configs",
    )
    op.drop_table("evaluation_judge_configs")
