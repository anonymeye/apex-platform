"""Base vector store protocol."""

from abc import ABC, abstractmethod

from conduit.rag.splitters import Document


class VectorStore(ABC):
    """Abstract base class for vector stores."""

    @abstractmethod
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
        ...

    @abstractmethod
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
        ...

    @abstractmethod
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
        ...

    @abstractmethod
    async def delete(self, ids: list[str]) -> bool:
        """Delete documents by IDs.

        Args:
            ids: List of document IDs to delete

        Returns:
            True if successful
        """
        ...
