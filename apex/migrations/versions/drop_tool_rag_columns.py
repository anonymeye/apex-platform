"""Drop RAG-specific columns from tools (generic Tool)

Revision ID: drop_tool_rag_cols
Revises: ce486ea2174c
Create Date: 2026-01-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "drop_tool_rag_cols"
down_revision: Union[str, None] = "ce486ea2174c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("tools", "rag_template")
    op.drop_column("tools", "rag_k")
    op.drop_column("tools", "auto_created")


def downgrade() -> None:
    op.add_column("tools", sa.Column("rag_template", sa.Text(), nullable=True))
    op.add_column("tools", sa.Column("rag_k", sa.Integer(), nullable=True))
    op.add_column("tools", sa.Column("auto_created", sa.Boolean(), nullable=False, server_default=sa.false()))
