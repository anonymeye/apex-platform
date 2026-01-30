"""Tests for embedding models."""

import pytest

from conduit.core.protocols import Embeddable
from conduit.rag.embeddings import EmbeddingModel


class MockEmbeddable(Embeddable):
    """Mock embeddable for testing."""

    def __init__(self, embeddings: list[list[float]] | None = None):
        """Initialize mock embeddable."""
        self.embeddings = embeddings or [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]

    async def embed(self, texts: str | list[str], options: dict | None = None) -> dict:
        """Return mock embeddings."""
        if isinstance(texts, str):
            return {"embeddings": [self.embeddings[0]]}
        return {"embeddings": self.embeddings[: len(texts)]}


@pytest.mark.asyncio
async def test_embed_texts_single():
    """Test embedding single text."""
    mock = MockEmbeddable()
    model = EmbeddingModel(mock)

    embeddings = await model.embed_texts(["text1"])
    assert len(embeddings) == 1
    assert embeddings[0] == [0.1, 0.2, 0.3]


@pytest.mark.asyncio
async def test_embed_texts_multiple():
    """Test embedding multiple texts."""
    mock = MockEmbeddable()
    model = EmbeddingModel(mock)

    embeddings = await model.embed_texts(["text1", "text2"])
    assert len(embeddings) == 2
    assert embeddings[0] == [0.1, 0.2, 0.3]
    assert embeddings[1] == [0.4, 0.5, 0.6]


@pytest.mark.asyncio
async def test_embed_texts_batch():
    """Test embedding with batching."""
    mock = MockEmbeddable([[0.1] * 3, [0.2] * 3, [0.3] * 3, [0.4] * 3])
    model = EmbeddingModel(mock)

    embeddings = await model.embed_texts(["t1", "t2", "t3", "t4"], batch_size=2)
    assert len(embeddings) == 4


@pytest.mark.asyncio
async def test_embed_query():
    """Test embedding query."""
    mock = MockEmbeddable()
    model = EmbeddingModel(mock)

    embedding = await model.embed_query("query text")
    assert embedding == [0.1, 0.2, 0.3]


@pytest.mark.asyncio
async def test_embed_documents():
    """Test embedding documents."""
    mock = MockEmbeddable()
    model = EmbeddingModel(mock)

    embeddings = await model.embed_documents(["doc1", "doc2"])
    assert len(embeddings) == 2


@pytest.mark.asyncio
async def test_embed_texts_empty():
    """Test embedding empty list."""
    mock = MockEmbeddable()
    model = EmbeddingModel(mock)

    embeddings = await model.embed_texts([])
    assert embeddings == []


@pytest.mark.asyncio
async def test_embed_missing_embeddings_key():
    """Test error when embeddings key is missing."""
    class BadEmbeddable(Embeddable):
        async def embed(self, texts: str | list[str], options: dict | None = None) -> dict:
            return {}

    model = EmbeddingModel(BadEmbeddable())

    with pytest.raises(ValueError, match="did not return 'embeddings' key"):
        await model.embed_texts(["text"])
