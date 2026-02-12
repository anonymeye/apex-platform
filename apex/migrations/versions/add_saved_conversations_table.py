"""Add saved_conversations table (Plan B.1).

Revision ID: add_saved_conversations
Revises: add_human_reviewed_at
Create Date: 2026-02-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "add_saved_conversations"
down_revision: Union[str, None] = "add_human_reviewed_at"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "saved_conversations",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=True),
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
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_saved_conversations_conversation_id"),
        "saved_conversations",
        ["conversation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_saved_conversations_created_at"),
        "saved_conversations",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_saved_conversations_organization_id"),
        "saved_conversations",
        ["organization_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_saved_conversations_organization_id"),
        table_name="saved_conversations",
    )
    op.drop_index(
        op.f("ix_saved_conversations_created_at"),
        table_name="saved_conversations",
    )
    op.drop_index(
        op.f("ix_saved_conversations_conversation_id"),
        table_name="saved_conversations",
    )
    op.drop_table("saved_conversations")
