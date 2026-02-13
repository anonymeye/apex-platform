"""Add messages snapshot column to saved_conversations.

Revision ID: add_messages_saved_conv
Revises: add_saved_conversations
Create Date: 2026-02-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "add_messages_saved_conv"
down_revision: Union[str, None] = "add_saved_conversations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "saved_conversations",
        sa.Column("messages", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("saved_conversations", "messages")
