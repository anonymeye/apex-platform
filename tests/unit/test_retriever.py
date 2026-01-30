"""Tests for retrievers."""

import pytest

from conduit.rag.embeddings import EmbeddingModel
from conduit.rag.retriever import RetrievalResult, Retriever, VectorRetriever
from conduit.rag.splitters import Document
from conduit.rag.stores.memory import MemoryVectorStore


class MockEmbeddable:
    """Mock embeddable for testing."""

    async def embed(self, texts: str | list[str], options: dict | None = None) -> dict:
        """Return mock embeddings."""
        if isinstance(texts, str):
            return {"embeddings": [[0.1, 0.2, 0.3]]}
        return {"embeddings": [[0.1, 0.2, 0.3]] * len(texts)}


@pytest.mark.asyncio
async def test_vector_retriever_basic():
    """Test basic vector retriever."""
    store = MemoryVectorStore()
    embed_model = EmbeddingModel(MockEmbeddable())

    # Add documents
    docs = [
        Document(content="Python programming", metadata={"source": "test1.txt"}),
        Document(content="Machine learning", metadata={"source": "test2.txt"}),
    ]
    embeddings = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
    await store.add_documents(docs, embeddings)

    retriever = VectorRetriever(store, embed_model)
    results = await retriever.retrieve("Python", k=2)

    assert len(results) == 2
    assert all(isinstance(r, RetrievalResult) for r in results)
    assert all(isinstance(r.document, Document) for r in results)
    assert all(isinstance(r.score, float) for r in results)


@pytest.mark.asyncio
async def test_vector_retriever_k_parameter():
    """Test retriever with different k values."""
    store = MemoryVectorStore()
    embed_model = EmbeddingModel(MockEmbeddable())

    docs = [Document(content=f"Document {i}", metadata={}) for i in range(5)]
    embeddings = [[float(i), 0.0, 0.0] for i in range(5)]
    await store.add_documents(docs, embeddings)

    retriever = VectorRetriever(store, embed_model)

    results = await retriever.retrieve("query", k=3)
    assert len(results) == 3

    results = await retriever.retrieve("query", k=1)
    assert len(results) == 1


@pytest.mark.asyncio
async def test_retrieval_result_model():
    """Test RetrievalResult model."""
    doc = Document(content="Test", metadata={})
    result = RetrievalResult(document=doc, score=0.95)

    assert result.document == doc
    assert result.score == 0.95


def test_retriever_abstract():
    """Test that Retriever is abstract."""
    with pytest.raises(TypeError):
        Retriever()  # type: ignore
