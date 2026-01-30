"""Example: RAG (Retrieval-Augmented Generation) pipeline.

Demonstrates document retrieval and augmented generation.
"""

import asyncio
import os

from conduit.providers.mock import MockModel
from conduit.providers.openai import OpenAIModel
from conduit.rag import (
    Document,
    EmbeddingModel,
    MemoryVectorStore,
    RecursiveSplitter,
    RAGChain,
    VectorRetriever,
)


async def main() -> None:
    """Run RAG pipeline example."""
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Sample documents
    documents = [
        Document(
            content="Python is a high-level programming language known for its simplicity.",
            metadata={"source": "intro.txt"}
        ),
        Document(
            content="Conduit is a library for orchestrating LLM interactions in Python.",
            metadata={"source": "conduit.txt"}
        ),
        Document(
            content="RAG combines retrieval of relevant documents with language model generation.",
            metadata={"source": "rag.txt"}
        ),
    ]
    
    # Split documents
    splitter = RecursiveSplitter(chunk_size=100, chunk_overlap=20)
    chunks = []
    for doc in documents:
        chunks.extend(splitter.split(doc.content))
    
    # Create vector store
    store = MemoryVectorStore()
    
    if api_key:
        chat_model = OpenAIModel(api_key=api_key, model="gpt-4")
        # Create embedding model (using chat model for embeddings)
        embedding_model = EmbeddingModel(chat_model)
        
        # Add documents to store
        for chunk in chunks:
            embedding = await embedding_model.embed(chunk)
            store.add(embedding["embeddings"][0], metadata={"text": chunk})
        
        # Create RAG chain
        retriever = VectorRetriever(store, embedding_model)
        chain = RAGChain(model=chat_model, retriever=retriever)
        
        # Query
        response = await chain.query("What is Python?")
        print("RAG Response:", response.extract_content())
    else:
        # Mock RAG for demonstration
        from conduit.core.protocols import Embeddable
        from typing import Any
        
        class MockEmbedding(Embeddable):
            async def embed(self, texts: str | list[str], options: dict[str, Any] | None = None) -> dict[str, Any]:
                if isinstance(texts, str):
                    texts = [texts]
                # Simple mock embeddings
                return {"embeddings": [[0.1] * 128 for _ in texts]}
        
        chat_model = MockModel(response_content="Python is a high-level programming language known for its simplicity.")
        embedding_model = MockEmbedding()
        
        # Add documents
        for chunk in chunks:
            embedding = await embedding_model.embed(chunk)
            store.add(embedding["embeddings"][0], metadata={"text": chunk})
        
        retriever = VectorRetriever(store, embedding_model)
        chain = RAGChain(model=chat_model, retriever=retriever)
        
        response = await chain.query("What is Python?")
        print("RAG Response:", response.extract_content())
        print("(Using mock models - set OPENAI_API_KEY for real RAG)")


if __name__ == "__main__":
    asyncio.run(main())
