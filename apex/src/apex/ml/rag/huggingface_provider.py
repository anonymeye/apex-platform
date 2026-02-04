"""HuggingFace embedding provider implementation."""

import asyncio
import logging
from typing import Any, List, Optional

from conduit.core.protocols import Embeddable
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class HuggingFaceProvider(Embeddable):
    """HuggingFace embedding provider implementing Embeddable protocol."""

    def __init__(self, model: str, batch_size: int = 32):
        """Initialize HuggingFace provider.

        Args:
            model: Model name to load (e.g., 'all-MiniLM-L6-v2')
            batch_size: Default batch size for embedding operations (default: 32)
        """
        logger.info(f"Loading HuggingFace model: {model}")
        try:
            self.transformer = SentenceTransformer(model)
            self.model = model
            self.batch_size = batch_size
            # Get embedding dimension from model
            self.dimension = self.transformer.get_sentence_embedding_dimension()
            logger.info(
                f"HuggingFace model '{model}' loaded successfully "
                f"(dimension: {self.dimension})"
            )
        except Exception as e:
            logger.error(f"Failed to load HuggingFace model '{model}': {e}")
            raise

    async def embed(
        self, texts: str | List[str], options: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Generate embeddings for text(s).

        Args:
            texts: Single text string or list of text strings
            options: Optional embedding options (can include 'batch_size')

        Returns:
            Dictionary with 'embeddings' key containing list of embedding vectors
        """
        # Extract batch_size from options or use default
        batch_size = (options or {}).get("batch_size", self.batch_size)

        # Normalize to list
        if isinstance(texts, str):
            texts_list = [texts]
        else:
            texts_list = texts

        if not texts_list:
            return {"embeddings": []}

        # Run in thread pool to avoid blocking
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop, create new one
            loop = asyncio.get_event_loop()

        embeddings = await loop.run_in_executor(
            None,
            lambda: self.transformer.encode(
                texts_list,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=False,
            ),
        )

        # Convert to list of lists
        embeddings_list = embeddings.tolist()

        return {"embeddings": embeddings_list}

    async def embed_batch(
        self,
        texts: List[str],
        batch_size: Optional[int] = None,
    ) -> List[List[float]]:
        """Embed multiple texts in batch (convenience method).

        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing (defaults to instance batch_size)

        Returns:
            List of embedding vectors (each is a list of floats)
        """
        options = {"batch_size": batch_size} if batch_size is not None else None
        result = await self.embed(texts, options=options)
        return result["embeddings"]
