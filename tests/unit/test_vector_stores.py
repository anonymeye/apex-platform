"""Tests for vector stores."""

import pytest

from conduit.rag.splitters import Document
from conduit.rag.stores.memory import MemoryVectorStore


@pytest.mark.asyncio
async def test_add_documents():
    """Test adding documents to store."""
    store = MemoryVectorStore()
    docs = [
        Document(content="Hello world", metadata={"source": "test1.txt"}),
        Document(content="Python is great", metadata={"source": "test2.txt"}),
    ]
    embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]

    ids = await store.add_documents(docs, embeddings)
    assert len(ids) == 2
    assert len(store) == 2


@pytest.mark.asyncio
async def test_add_documents_with_ids():
    """Test adding documents with custom IDs."""
    store = MemoryVectorStore()
    docs = [Document(content="Test", metadata={})]
    embeddings = [[0.1, 0.2, 0.3]]
    ids = await store.add_documents(docs, embeddings, ids=["custom-id"])

    assert ids == ["custom-id"]
    assert len(store) == 1


@pytest.mark.asyncio
async def test_add_documents_length_mismatch():
    """Test error on documents/embeddings length mismatch."""
    store = MemoryVectorStore()
    docs = [Document(content="Test", metadata={})]
    embeddings = [[0.1, 0.2], [0.3, 0.4]]

    with pytest.raises(ValueError, match="length mismatch"):
        await store.add_documents(docs, embeddings)


@pytest.mark.asyncio
async def test_similarity_search():
    """Test similarity search."""
    store = MemoryVectorStore()
    docs = [
        Document(content="Python programming", metadata={"source": "test1.txt"}),
        Document(content="Machine learning", metadata={"source": "test2.txt"}),
        Document(content="Data science", metadata={"source": "test3.txt"}),
    ]
    # Use simple embeddings for testing
    embeddings = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    await store.add_documents(docs, embeddings)

    # Query similar to first document
    query_embedding = [0.9, 0.1, 0.0]
    results = await store.similarity_search(query_embedding, k=2)

    assert len(results) == 2
    assert all(isinstance(doc, Document) for doc in results)


@pytest.mark.asyncio
async def test_similarity_search_with_score():
    """Test similarity search with scores."""
    store = MemoryVectorStore()
    docs = [Document(content="Test", metadata={})]
    embeddings = [[1.0, 0.0, 0.0]]
    await store.add_documents(docs, embeddings)

    query_embedding = [1.0, 0.0, 0.0]  # Same as document
    results = await store.similarity_search_with_score(query_embedding, k=1)

    assert len(results) == 1
    doc, score = results[0]
    assert isinstance(doc, Document)
    assert isinstance(score, float)
    assert score > 0.9  # Should be very similar


@pytest.mark.asyncio
async def test_similarity_search_with_filter():
    """Test similarity search with metadata filter."""
    store = MemoryVectorStore()
    docs = [
        Document(content="Python", metadata={"category": "programming"}),
        Document(content="Machine learning", metadata={"category": "ai"}),
    ]
    embeddings = [[1.0, 0.0], [0.0, 1.0]]
    await store.add_documents(docs, embeddings)

    query_embedding = [1.0, 0.0]
    results = await store.similarity_search(query_embedding, k=5, filter={"category": "programming"})

    assert len(results) == 1
    assert results[0].metadata["category"] == "programming"


@pytest.mark.asyncio
async def test_delete():
    """Test deleting documents."""
    store = MemoryVectorStore()
    docs = [Document(content="Test", metadata={})]
    embeddings = [[0.1, 0.2, 0.3]]
    ids = await store.add_documents(docs, embeddings)

    assert len(store) == 1

    success = await store.delete(ids)
    assert success is True
    assert len(store) == 0


@pytest.mark.asyncio
async def test_delete_multiple():
    """Test deleting multiple documents."""
    store = MemoryVectorStore()
    docs = [
        Document(content="Test1", metadata={}),
        Document(content="Test2", metadata={}),
        Document(content="Test3", metadata={}),
    ]
    embeddings = [[0.1] * 3, [0.2] * 3, [0.3] * 3]
    ids = await store.add_documents(docs, embeddings)

    assert len(store) == 3

    await store.delete(ids[:2])
    assert len(store) == 1


@pytest.mark.asyncio
async def test_cosine_similarity():
    """Test cosine similarity calculation."""
    store = MemoryVectorStore()
    docs = [Document(content="Test", metadata={})]
    embeddings = [[1.0, 0.0, 0.0]]
    await store.add_documents(docs, embeddings)

    # Same vector should have similarity of 1.0
    query_embedding = [1.0, 0.0, 0.0]
    results = await store.similarity_search_with_score(query_embedding, k=1)
    assert results[0][1] == pytest.approx(1.0, abs=0.01)

    # Orthogonal vector should have similarity of 0.0
    query_embedding = [0.0, 1.0, 0.0]
    results = await store.similarity_search_with_score(query_embedding, k=1)
    assert results[0][1] == pytest.approx(0.0, abs=0.01)
