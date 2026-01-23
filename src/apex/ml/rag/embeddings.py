"""Embedding service wrapper."""

import logging
from typing import Any

from conduit.rag import EmbeddingModel

from apex.ml.rag.huggingface_provider import HuggingFaceProvider

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", batch_size: int = 32):
        """Initialize embedding service.

        Args:
            model_name: HuggingFace model name for embeddings
            batch_size: Batch size for embedding operations
        """
        self.provider = HuggingFaceProvider(model_name, batch_size)
        self.embedding_model = EmbeddingModel(self.provider)
        logger.info(f"Initialized embedding service with model: {model_name}")

    async def embed(self, texts: str | list[str]) -> dict[str, Any]:
        """Generate embeddings for text(s).

        Args:
            texts: Single text string or list of text strings

        Returns:
            Dictionary with 'embeddings' key
        """
        return await self.embedding_model.embed(texts)

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple documents.

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors
        """
        result = await self.embedding_model.embed(texts)
        return result["embeddings"]
