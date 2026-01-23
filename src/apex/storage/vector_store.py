"""Vector store interface & implementations."""

import logging
from typing import Optional
from uuid import UUID

from conduit.rag import Document, MemoryVectorStore, VectorStore

logger = logging.getLogger(__name__)


class ApexVectorStore:
    """Wrapper around vector store with knowledge base filtering."""

    def __init__(self, vector_store: VectorStore):
        """Initialize vector store wrapper.

        Args:
            vector_store: Underlying vector store implementation
        """
        self.store = vector_store
        logger.info("Initialized Apex vector store")

    async def add_documents(
        self,
        documents: list[Document],
        embeddings: list[list[float]],
        knowledge_base_id: Optional[UUID] = None,
    ) -> list[str]:
        """Add documents to vector store.

        Args:
            documents: List of documents to add
            embeddings: List of embedding vectors
            knowledge_base_id: Optional knowledge base ID for filtering

        Returns:
            List of document IDs
        """
        # Add knowledge_base_id to document metadata if provided
        if knowledge_base_id:
            for doc in documents:
                if doc.metadata is None:
                    doc.metadata = {}
                doc.metadata["knowledge_base_id"] = str(knowledge_base_id)

        return await self.store.add_documents(documents, embeddings)

    async def search(
        self,
        query_embedding: list[float],
        k: int = 5,
        knowledge_base_id: Optional[UUID] = None,
    ) -> list[Document]:
        """Search for similar documents.

        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            knowledge_base_id: Optional knowledge base ID for filtering

        Returns:
            List of similar documents
        """
        filter_dict = None
        if knowledge_base_id:
            filter_dict = {"knowledge_base_id": str(knowledge_base_id)}

        return await self.store.similarity_search(
            query_embedding, k=k, filter=filter_dict
        )

    async def search_with_score(
        self,
        query_embedding: list[float],
        k: int = 5,
        knowledge_base_id: Optional[UUID] = None,
    ) -> list[tuple[Document, float]]:
        """Search for similar documents with scores.

        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            knowledge_base_id: Optional knowledge base ID for filtering

        Returns:
            List of (document, score) tuples
        """
        filter_dict = None
        if knowledge_base_id:
            filter_dict = {"knowledge_base_id": str(knowledge_base_id)}

        return await self.store.similarity_search_with_score(
            query_embedding, k=k, filter=filter_dict
        )
