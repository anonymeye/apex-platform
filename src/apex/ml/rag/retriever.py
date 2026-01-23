"""Custom retriever with schema awareness."""

import logging
from typing import Optional
from uuid import UUID

from conduit.rag import Document, VectorRetriever

from apex.storage.vector_store import ApexVectorStore

logger = logging.getLogger(__name__)


class KnowledgeBaseRetriever(VectorRetriever):
    """Retriever for a specific knowledge base."""

    def __init__(
        self,
        vector_store: ApexVectorStore,
        embedding_model,
        knowledge_base_id: Optional[UUID] = None,
    ):
        """Initialize knowledge base retriever.

        Args:
            vector_store: ApexVectorStore instance
            embedding_model: Embedding model for queries
            knowledge_base_id: Optional knowledge base ID for filtering
        """
        # Create a wrapper that filters by knowledge_base_id
        self.knowledge_base_id = knowledge_base_id
        self.apex_store = vector_store

        # Initialize parent with the underlying store
        super().__init__(store=vector_store.store, embedding_model=embedding_model)

    async def retrieve(
        self, query: str, k: int = 5
    ) -> list[tuple[Document, float]]:
        """Retrieve documents for a query.

        Args:
            query: Query string
            k: Number of documents to retrieve

        Returns:
            List of (document, score) tuples
        """
        # Generate query embedding
        embedding_result = await self.embedding_model.embed(query)
        query_embedding = embedding_result["embeddings"][0]

        # Search with knowledge base filter
        results = await self.apex_store.search_with_score(
            query_embedding, k=k, knowledge_base_id=self.knowledge_base_id
        )

        return results
