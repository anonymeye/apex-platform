"""Add human_reviewed_at to evaluation_scores (Phase 2.2).

Revision ID: add_human_reviewed_at
Revises: add_evaluation_tables
Create Date: 2026-02-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "add_human_reviewed_at"
down_revision: Union[str, None] = "add_evaluation_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "evaluation_scores",
        sa.Column("human_reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("evaluation_scores", "human_reviewed_at")
