"""pgvector-backed VectorStore implementation.

Implements conduit's VectorStore protocol so apex can use persistent
vector storage. Swapping to another backend (e.g. Qdrant) only requires
a new class implementing the same interface and a config change.
"""

import logging
import uuid
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from conduit.rag.splitters import Document
from conduit.rag.stores.base import VectorStore

logger = logging.getLogger(__name__)


def _embedding_to_pg(embedding: list[float]) -> str:
    """Format embedding for PostgreSQL vector literal."""
    return "[" + ",".join(str(x) for x in embedding) + "]"


class PgVectorStore(VectorStore):
    """Persistent vector store using PostgreSQL + pgvector.

    Implements conduit.rag.stores.base.VectorStore. Uses the same database
    as apex; table and dimension are configurable for easy migration.
    """

    def __init__(
        self,
        database_url: str,
        *,
        table_name: str = "vector_embeddings",
        embedding_dimension: int = 384,
    ):
        """Initialize pgvector store.

        Args:
            database_url: Async PostgreSQL URL (postgresql+asyncpg://...).
            table_name: Table name for embeddings (default from config).
            embedding_dimension: Vector dimension; must match your embedding model.
        """
        self._engine = create_async_engine(database_url, pool_pre_ping=True)
        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        self._table = table_name
        self._dim = embedding_dimension
        logger.info(
            "Initialized PgVectorStore table=%s dimension=%s",
            table_name,
            embedding_dimension,
        )

    async def add_documents(
        self,
        documents: list[Document],
        embeddings: list[list[float]],
        *,
        ids: list[str] | None = None,
    ) -> list[str]:
        if len(documents) != len(embeddings):
            raise ValueError(
                f"Documents ({len(documents)}) and embeddings ({len(embeddings)}) length mismatch"
            )
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]
        elif len(ids) != len(documents):
            raise ValueError(
                f"IDs ({len(ids)}) and documents ({len(documents)}) length mismatch"
            )

        async with self._session_factory() as session:
            for doc_id, doc, embedding in zip(ids, documents, embeddings, strict=True):
                meta = doc.metadata or {}
                emb_str = _embedding_to_pg(embedding)
                await session.execute(
                    text(
                        f"""
                        INSERT INTO {self._table} (id, embedding, content, metadata)
                        VALUES (:id, CAST(:embedding AS vector), :content, CAST(:meta_json AS jsonb))
                        ON CONFLICT (id) DO UPDATE SET
                            embedding = EXCLUDED.embedding,
                            content = EXCLUDED.content,
                            metadata = EXCLUDED.metadata
                        """
                    ),
                    {
                        "id": doc_id,
                        "embedding": emb_str,
                        "content": doc.content,
                        "meta_json": _metadata_to_json(meta),
                    },
                )
            await session.commit()
        return ids

    async def similarity_search(
        self,
        query_embedding: list[float],
        *,
        k: int = 5,
        filter: dict[str, str] | None = None,
    ) -> list[Document]:
        results = await self.similarity_search_with_score(
            query_embedding, k=k, filter=filter
        )
        return [doc for doc, _ in results]

    async def similarity_search_with_score(
        self,
        query_embedding: list[float],
        *,
        k: int = 5,
        filter: dict[str, str] | None = None,
    ) -> list[tuple[Document, float]]:
        q_emb = _embedding_to_pg(query_embedding)
        where_clause = ""
        params: dict = {"q": q_emb, "k": k}
        if filter:
            # Build WHERE for metadata (allowlist keys to avoid SQL injection)
            allowed_keys = {"knowledge_base_id"}
            conditions = []
            for i, (key, value) in enumerate(filter.items()):
                if key not in allowed_keys:
                    continue
                param_key = f"meta_{i}"
                conditions.append(f"(metadata->>'{key}') = :{param_key}")
                params[param_key] = value
            if conditions:
                where_clause = " WHERE " + " AND ".join(conditions)

        # Cosine distance <=>; similarity = 1 - distance (use CAST to avoid :q:: parsed as param)
        sql = text(
            f"""
            SELECT id, content, metadata,
                   (1 - (embedding <=> CAST(:q AS vector))) AS similarity
            FROM {self._table}
            {where_clause}
            ORDER BY embedding <=> CAST(:q AS vector)
            LIMIT :k
            """
        )
        async with self._session_factory() as session:
            result = await session.execute(sql, params)
            rows = result.mappings().all()

        out: list[tuple[Document, float]] = []
        for row in rows:
            meta = row["metadata"] or {}
            if not isinstance(meta, dict):
                meta = dict(meta) if meta else {}
            meta_str = {str(k): str(v) for k, v in meta.items()}
            doc = Document(content=row["content"], metadata=meta_str)
            out.append((doc, float(row["similarity"])))
        return out

    async def delete(self, ids: list[str]) -> bool:
        if not ids:
            return True
        async with self._session_factory() as session:
            await session.execute(
                text(f"DELETE FROM {self._table} WHERE id = ANY(:ids)"),
                {"ids": ids},
            )
            await session.commit()
        return True

    async def close(self) -> None:
        """Close the engine (e.g. on app shutdown)."""
        await self._engine.dispose()


def _metadata_to_json(meta: dict) -> str:
    """Serialize metadata dict to JSON string for jsonb."""
    import json
    return json.dumps(meta)
