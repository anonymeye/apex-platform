"""RAG chain orchestration."""

import logging
from typing import Optional

from conduit.rag import RAGChain, VectorRetriever

logger = logging.getLogger(__name__)


class RAGPipeline:
    """RAG pipeline for document retrieval and generation."""

    def __init__(
        self,
        retriever: VectorRetriever,
        chat_model,
        default_template: Optional[str] = None,
        default_k: int = 5,
    ):
        """Initialize RAG pipeline.

        Args:
            retriever: VectorRetriever instance
            chat_model: ChatModel for generation
            default_template: Default RAG template
            default_k: Default number of chunks to retrieve
        """
        self.retriever = retriever
        self.chat_model = chat_model
        self.default_template = default_template or (
            "Use the following context to answer the question. "
            "If you cannot answer based on the context, say so.\n\n"
            "Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
        )
        self.default_k = default_k

    def create_rag_chain(
        self, template: Optional[str] = None, k: Optional[int] = None
    ) -> RAGChain:
        """Create a RAG chain with specified parameters.

        Args:
            template: RAG template (uses default if not provided)
            k: Number of chunks to retrieve (uses default if not provided)

        Returns:
            RAGChain instance
        """
        return RAGChain(
            model=self.chat_model,
            retriever=self.retriever,
            template=template or self.default_template,
            k=k or self.default_k,
        )
