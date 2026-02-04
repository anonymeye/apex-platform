"""In-memory vector store implementation."""

import uuid

import numpy as np

from conduit.rag.splitters import Document
from conduit.rag.stores.base import VectorStore


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Calculate cosine similarity between two vectors.

    Args:
        a: First vector
        b: Second vector

    Returns:
        Cosine similarity score (0-1)
    """
    a_arr = np.array(a, dtype=np.float32)
    b_arr = np.array(b, dtype=np.float32)

    dot_product = np.dot(a_arr, b_arr)
    norm_a = np.linalg.norm(a_arr)
    norm_b = np.linalg.norm(b_arr)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(dot_product / (norm_a * norm_b))


class MemoryVectorStore(VectorStore):
    """In-memory vector store using cosine similarity.

    Examples:
        >>> store = MemoryVectorStore()
        >>> ids = await store.add_documents(docs, embeddings)
        >>> results = await store.similarity_search(query_embedding, k=5)
    """

    def __init__(self) -> None:
        """Initialize in-memory vector store."""
        self._documents: dict[str, Document] = {}
        self._embeddings: dict[str, list[float]] = {}

    async def add_documents(
        self,
        documents: list[Document],
        embeddings: list[list[float]],
        *,
        ids: list[str] | None = None,
    ) -> list[str]:
        """Add documents with embeddings to the store.

        Args:
            documents: List of documents to add
            embeddings: List of embedding vectors (one per document)
            ids: Optional list of document IDs (auto-generated if None)

        Returns:
            List of document IDs

        Raises:
            ValueError: If documents and embeddings length mismatch
        """
        if len(documents) != len(embeddings):
            raise ValueError(
                f"Documents ({len(documents)}) and embeddings ({len(embeddings)}) length mismatch"
            )

        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]
        elif len(ids) != len(documents):
            raise ValueError(f"IDs ({len(ids)}) and documents ({len(documents)}) length mismatch")

        for doc_id, doc, embedding in zip(ids, documents, embeddings, strict=True):
            self._documents[doc_id] = doc
            self._embeddings[doc_id] = embedding

        return ids

    async def similarity_search(
        self, query_embedding: list[float], *, k: int = 5, filter: dict[str, str] | None = None
    ) -> list[Document]:
        """Search for similar documents.

        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            filter: Optional metadata filter

        Returns:
            List of similar documents
        """
        results_with_scores = await self.similarity_search_with_score(
            query_embedding, k=k, filter=filter
        )
        return [doc for doc, _ in results_with_scores]

    async def similarity_search_with_score(
        self, query_embedding: list[float], *, k: int = 5, filter: dict[str, str] | None = None
    ) -> list[tuple[Document, float]]:
        """Search for similar documents with similarity scores.

        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            filter: Optional metadata filter

        Returns:
            List of (document, score) tuples, sorted by score (highest first)
        """
        scores: list[tuple[str, float]] = []

        for doc_id, embedding in self._embeddings.items():
            doc = self._documents[doc_id]

            # Apply filter if provided
            if filter:
                if not all(doc.metadata.get(key) == value for key, value in filter.items()):
                    continue

            similarity = _cosine_similarity(query_embedding, embedding)
            scores.append((doc_id, similarity))

        # Sort by score (highest first) and take top k
        scores.sort(key=lambda x: x[1], reverse=True)
        top_k = scores[:k]

        # Return documents with scores
        results = [(self._documents[doc_id], score) for doc_id, score in top_k]
        return results

    async def delete(self, ids: list[str]) -> bool:
        """Delete documents by IDs.

        Args:
            ids: List of document IDs to delete

        Returns:
            True if successful
        """
        for doc_id in ids:
            self._documents.pop(doc_id, None)
            self._embeddings.pop(doc_id, None)

        return True

    def __len__(self) -> int:
        """Return number of documents in store."""
        return len(self._documents)
