"""Embedding models for RAG."""

from conduit.core.protocols import Embeddable


class EmbeddingModel:
    """Wrapper around Embeddable protocol for RAG use.

    Examples:
        >>> model = EmbeddingModel(embed_model)
        >>> embeddings = await model.embed_texts(["text1", "text2"])
        >>> query_embedding = await model.embed_query("query text")
    """

    def __init__(self, embeddable: Embeddable):
        """Initialize embedding model.

        Args:
            embeddable: Embeddable instance (e.g., OpenAI embeddings)
        """
        self.embeddable = embeddable

    async def embed_texts(
        self, texts: list[str], *, batch_size: int | None = None
    ) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of text strings to embed
            batch_size: Optional batch size for processing (None = process all at once)

        Returns:
            List of embedding vectors (each is a list of floats)

        Raises:
            ProviderError: If embedding generation fails
        """
        if not texts:
            return []

        if batch_size is None:
            # Process all at once
            result = await self.embeddable.embed(texts)
            embeddings = result.get("embeddings", [])
            if not embeddings:
                raise ValueError("Embedding model did not return 'embeddings' key")
            # Type assertion for mypy
            if not isinstance(embeddings, list) or not all(isinstance(e, list) for e in embeddings):
                raise ValueError("Embeddings must be a list of lists")
            return list(embeddings)

        # Process in batches
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            result = await self.embeddable.embed(batch)
            batch_embeddings = result.get("embeddings", [])
            if not batch_embeddings:
                raise ValueError("Embedding model did not return 'embeddings' key")
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    async def embed_query(self, text: str) -> list[float]:
        """Generate embedding for a single query text.

        Args:
            text: Query text to embed

        Returns:
            Embedding vector as list of floats

        Raises:
            ProviderError: If embedding generation fails
        """
        result = await self.embeddable.embed(text)
        embeddings = result.get("embeddings", [])

        if not embeddings:
            raise ValueError("Embedding model did not return 'embeddings' key")

        # If single text, should return single embedding
        if isinstance(embeddings, list) and len(embeddings) > 0:
            if isinstance(embeddings[0], list):
                return embeddings[0]
            return embeddings

        raise ValueError("Unexpected embedding format")

    async def embed_documents(self, documents: list[str]) -> list[list[float]]:
        """Generate embeddings for documents (alias for embed_texts).

        Args:
            documents: List of document texts to embed

        Returns:
            List of embedding vectors
        """
        return await self.embed_texts(documents)
