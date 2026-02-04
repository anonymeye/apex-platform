"""Integration tests for RAG chain."""

import pytest

from conduit.core.protocols import ChatModel, ModelInfo, Capabilities
from conduit.rag.chain import DEFAULT_TEMPLATE, RAGChain
from conduit.rag.embeddings import EmbeddingModel
from conduit.rag.retriever import VectorRetriever
from conduit.rag.splitters import Document
from conduit.rag.stores.memory import MemoryVectorStore
from conduit.schema.messages import Message
from conduit.schema.responses import Response, Usage


class MockChatModel(ChatModel):
    """Mock chat model for testing."""

    def __init__(self, response_content: str = "Mock response"):
        """Initialize mock model."""
        self.response_content = response_content

    async def chat(self, messages: list[Message], options=None) -> Response:
        """Return mock response."""
        return Response(
            content=self.response_content,
            usage=Usage(input_tokens=10, output_tokens=5),
        )

    async def stream(self, messages: list[Message], options=None):
        """Not implemented."""
        raise NotImplementedError

    def model_info(self) -> ModelInfo:
        """Return mock model info."""
        return ModelInfo(
            provider="mock",
            model="mock-model",
            capabilities=Capabilities(),
        )


class MockEmbeddable:
    """Mock embeddable for testing."""

    async def embed(self, texts: str | list[str], options: dict | None = None) -> dict:
        """Return mock embeddings."""
        if isinstance(texts, str):
            return {"embeddings": [[0.1, 0.2, 0.3]]}
        # Return same embedding for all texts
        return {"embeddings": [[0.1, 0.2, 0.3]] * len(texts)}


@pytest.mark.asyncio
async def test_rag_chain_basic():
    """Test basic RAG chain execution."""
    # Setup
    store = MemoryVectorStore()
    embed_model = EmbeddingModel(MockEmbeddable())
    model = MockChatModel("This is the answer based on the context.")

    # Add documents
    docs = [
        Document(content="Python is a programming language", metadata={"source": "doc1.txt"}),
        Document(content="Machine learning uses algorithms", metadata={"source": "doc2.txt"}),
    ]
    embeddings = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
    await store.add_documents(docs, embeddings)

    # Create retriever and chain
    retriever = VectorRetriever(store, embed_model)
    chain = RAGChain(model=model, retriever=retriever, k=2)

    # Execute
    result = await chain("What is Python?")

    assert "answer" in result
    assert "sources" in result
    assert "usage" in result
    assert "scores" in result
    assert result["answer"] == "This is the answer based on the context."
    assert len(result["sources"]) == 2
    assert isinstance(result["usage"], Usage)
    assert len(result["scores"]) == 2


@pytest.mark.asyncio
async def test_rag_chain_custom_template():
    """Test RAG chain with custom template."""
    store = MemoryVectorStore()
    embed_model = EmbeddingModel(MockEmbeddable())
    model = MockChatModel("Custom answer")

    docs = [Document(content="Test", metadata={})]
    embeddings = [[1.0, 0.0, 0.0]]
    await store.add_documents(docs, embeddings)

    custom_template = "Context: {context}\n\nQuestion: {question}\n\nAnswer:"
    retriever = VectorRetriever(store, embed_model)
    chain = RAGChain(model=model, retriever=retriever, template=custom_template)

    result = await chain("Test question")
    assert result["answer"] == "Custom answer"


@pytest.mark.asyncio
async def test_rag_chain_custom_format_context():
    """Test RAG chain with custom context formatter."""
    store = MemoryVectorStore()
    embed_model = EmbeddingModel(MockEmbeddable())
    model = MockChatModel("Answer")

    docs = [Document(content="Test content", metadata={})]
    embeddings = [[1.0, 0.0, 0.0]]
    await store.add_documents(docs, embeddings)

    def custom_formatter(results):
        return "CUSTOM: " + " | ".join(r.document.content for r in results)

    retriever = VectorRetriever(store, embed_model)
    chain = RAGChain(
        model=model,
        retriever=retriever,
        format_context=custom_formatter,
    )

    result = await chain("Question")
    assert result["answer"] == "Answer"


@pytest.mark.asyncio
async def test_rag_chain_different_k():
    """Test RAG chain with different k values."""
    store = MemoryVectorStore()
    embed_model = EmbeddingModel(MockEmbeddable())
    model = MockChatModel("Answer")

    docs = [Document(content=f"Doc {i}", metadata={}) for i in range(5)]
    embeddings = [[float(i), 0.0, 0.0] for i in range(5)]
    await store.add_documents(docs, embeddings)

    retriever = VectorRetriever(store, embed_model)
    chain = RAGChain(model=model, retriever=retriever, k=3)

    result = await chain("Query")
    assert len(result["sources"]) == 3
    assert len(result["scores"]) == 3


@pytest.mark.asyncio
async def test_rag_chain_empty_results():
    """Test RAG chain with empty retrieval results."""
    store = MemoryVectorStore()
    embed_model = EmbeddingModel(MockEmbeddable())
    model = MockChatModel("Answer")

    retriever = VectorRetriever(store, embed_model)
    chain = RAGChain(model=model, retriever=retriever, k=5)

    result = await chain("Query")
    assert result["answer"] == "Answer"
    assert len(result["sources"]) == 0


def test_default_template():
    """Test default template format."""
    assert "{context}" in DEFAULT_TEMPLATE
    assert "{question}" in DEFAULT_TEMPLATE
