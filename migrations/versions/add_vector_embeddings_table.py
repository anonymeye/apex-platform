"""Add vector_embeddings table for pgvector store.

Revision ID: add_vector_embeddings
Revises: drop_tool_rag_cols
Create Date: 2026-01-29

"""
from typing import Sequence, Union

from alembic import op

revision: str = "add_vector_embeddings"
down_revision: Union[str, None] = "drop_tool_rag_cols"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Embedding dimension for all-MiniLM-L6-v2; change if using a different model
EMBEDDING_DIMENSION = 384


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        f"""
        CREATE TABLE vector_embeddings (
            id UUID PRIMARY KEY,
            embedding vector({EMBEDDING_DIMENSION}),
            content TEXT NOT NULL,
            metadata JSONB
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS vector_embeddings")
    # Optionally: op.execute("DROP EXTENSION IF EXISTS vector")
    # Leaving the extension in place is safer for other DB users
