"""Retriever implementations for RAG."""

from abc import ABC, abstractmethod

from pydantic import BaseModel

from conduit.rag.embeddings import EmbeddingModel
from conduit.rag.splitters import Document
from conduit.rag.stores.base import VectorStore


class RetrievalResult(BaseModel):
    """Result from document retrieval.

    Examples:
        >>> result = RetrievalResult(document=doc, score=0.95)
        >>> print(result.document.content)
    """

    document: Document
    score: float = 0.0


class Retriever(ABC):
    """Abstract base class for retrievers."""

    @abstractmethod
    async def retrieve(self, query: str, *, k: int = 5) -> list[RetrievalResult]:
        """Retrieve relevant documents for a query.

        Args:
            query: Query text
            k: Number of documents to retrieve

        Returns:
            List of retrieval results with documents and scores
        """
        ...


class VectorRetriever(Retriever):
    """Vector-based retriever using embeddings and vector store.

    Examples:
        >>> retriever = VectorRetriever(store=store, embedding_model=embed_model)
        >>> results = await retriever.retrieve("What is machine learning?", k=5)
    """

    def __init__(self, store: VectorStore, embedding_model: EmbeddingModel):
        """Initialize vector retriever.

        Args:
            store: Vector store instance
            embedding_model: Embedding model for query encoding
        """
        self.store = store
        self.embedding_model = embedding_model

    async def retrieve(self, query: str, *, k: int = 5) -> list[RetrievalResult]:
        """Retrieve relevant documents for a query.

        Args:
            query: Query text
            k: Number of documents to retrieve

        Returns:
            List of retrieval results with documents and scores
        """
        # Generate query embedding
        query_embedding = await self.embedding_model.embed_query(query)

        # Search vector store
        results = await self.store.similarity_search_with_score(query_embedding, k=k)

        # Convert to RetrievalResult
        return [RetrievalResult(document=doc, score=score) for doc, score in results]
