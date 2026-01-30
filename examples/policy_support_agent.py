"""Example: Customer Support Agent with Policy Retrieval using RAG.

This example demonstrates how to build a chat agent that retrieves policy rules
to reply to customer inquiries. The RAG system is integrated as a tool that the
agent can call when it needs to look up policy information.

Key concepts:
- RAG (Retrieval-Augmented Generation) for policy document retrieval
- Agent with tool calling capabilities
- Vector store for semantic search
- Integration of RAG as a tool in the agent loop
"""

import asyncio
import os
from typing import Any

from conduit.agent import make_agent
from conduit.core.protocols import ChatModel, Embeddable, ModelInfo, Capabilities
from conduit.providers.openai import OpenAIModel
from conduit.rag import (
    Document,
    EmbeddingModel,
    MemoryVectorStore,
    RecursiveSplitter,
    RAGChain,
    VectorRetriever,
)
from conduit.schema.messages import Message
from conduit.schema.responses import Response, Usage
from conduit.tools import Tool
from pydantic import BaseModel, Field


# ============================================================================
# Mock Embedding Model (for testing without API keys)
# ============================================================================

class MockEmbeddable(Embeddable):
    """Simple mock embedding model for demonstration.
    
    In production, use a real embedding model like OpenAI's text-embedding-ada-002.
    """

    async def embed(
        self, texts: str | list[str], options: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Generate simple mock embeddings."""
        if isinstance(texts, str):
            texts = [texts]
        
        # Simple hash-based embeddings for demo (not real embeddings)
        embeddings = []
        for text in texts:
            # Create a simple vector based on text hash
            import hashlib
            hash_val = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
            # Create 128-dim vector
            embedding = [(hash_val + i) % 100 / 100.0 for i in range(128)]
            embeddings.append(embedding)
        
        return {"embeddings": embeddings}


# ============================================================================
# Policy Document Loading
# ============================================================================

def load_policy_documents() -> list[Document]:
    """Load policy documents from files or database.
    
    In production, you would load these from files, a database, or an API.
    """
    policy_texts = [
        """
        Refund Policy:
        Customers can request refunds within 30 days of purchase for physical products.
        Digital products (software, ebooks, courses) are non-refundable unless defective.
        Refunds are processed within 5-7 business days to the original payment method.
        Partial refunds may be issued for items returned in used condition.
        """,
        """
        Shipping Policy:
        Standard shipping takes 5-7 business days and costs $5.99.
        Express shipping (2-3 business days) is available for $15.00.
        Overnight shipping (next business day) costs $25.00.
        Free shipping is available on orders over $50.00.
        International shipping rates vary by destination.
        """,
        """
        Return Policy:
        Items must be returned in original condition with all tags and packaging.
        Return requests must be made within 14 days of delivery date.
        Customer is responsible for return shipping costs unless item is defective.
        Refund will be issued once returned item is received and inspected.
        Electronics have a 30-day return window.
        """,
        """
        Warranty Policy:
        All products come with a 1-year manufacturer's warranty.
        Warranty covers defects in materials and workmanship.
        Warranty does not cover damage from misuse or normal wear and tear.
        Warranty claims must include proof of purchase and photos of the defect.
        """,
    ]
    
    # Split documents into chunks for better retrieval
    splitter = RecursiveSplitter(chunk_size=200, chunk_overlap=50)
    documents = []
    
    policy_types = ["refund", "shipping", "return", "warranty"]
    
    for i, text in enumerate(policy_texts):
        chunks = splitter.split_text(text.strip())
        for j, chunk in enumerate(chunks):
            documents.append(
                Document(
                    content=chunk,
                    metadata={
                        "policy_type": policy_types[i],
                        "source": f"policy_{policy_types[i]}.txt",
                        "chunk_index": j,
                    }
                )
            )
    
    return documents


# ============================================================================
# RAG System Setup
# ============================================================================

async def setup_rag_system(use_real_embeddings: bool = False) -> VectorRetriever:
    """Set up the RAG system with policy documents.
    
    Args:
        use_real_embeddings: If True, use OpenAI embeddings (requires API key).
                            If False, use mock embeddings for demonstration.
    
    Returns:
        Configured VectorRetriever instance
    """
    # Initialize vector store
    store = MemoryVectorStore()
    
    # Initialize embedding model
    if use_real_embeddings:
        # In production, use a real embedding model
        # For OpenAI, you would need to implement an Embeddable wrapper
        # around OpenAI's embeddings API
        raise NotImplementedError(
            "Real embeddings not implemented in this example. "
            "Use MockEmbeddable for demonstration or implement OpenAI embeddings."
        )
    else:
        embed_model = EmbeddingModel(MockEmbeddable())
    
    # Load and embed documents
    documents = load_policy_documents()
    document_texts = [doc.content for doc in documents]
    embeddings = await embed_model.embed_documents(document_texts)
    
    # Add to vector store
    await store.add_documents(documents, embeddings)
    
    print(f"✓ Loaded {len(documents)} policy document chunks into vector store")
    
    # Create retriever
    retriever = VectorRetriever(store=store, embedding_model=embed_model)
    
    return retriever


# ============================================================================
# RAG Tool Creation
# ============================================================================

class PolicySearchParams(BaseModel):
    """Parameters for policy search tool."""
    
    query: str = Field(
        description="The customer question or policy query to search for"
    )


async def create_policy_tool(
    model: ChatModel, retriever: VectorRetriever
) -> Tool:
    """Create a tool that searches policy documents using RAG.
    
    Args:
        model: ChatModel instance for generating answers
        retriever: VectorRetriever instance for document retrieval
    
    Returns:
        Tool instance that can be used by the agent
    """
    # Create RAG chain with policy-specific template
    policy_template = (
        "You are a customer support agent. Use the following policy information "
        "to answer the customer's question accurately and helpfully. "
        "If the information is not in the policies, say so clearly and offer "
        "to connect them with a human agent.\n\n"
        "Policy Information:\n{context}\n\n"
        "Customer Question: {question}\n\n"
        "Answer:"
    )
    
    rag_chain = RAGChain(
        model=model,
        retriever=retriever,
        template=policy_template,
        k=3,  # Retrieve top 3 policy chunks
    )
    
    async def search_policies(params: PolicySearchParams) -> str:
        """Search policy documents and return answer.
        
        This function is called by the agent when it decides to use the
        search_policy tool.
        """
        result = await rag_chain(params.query)
        
        # Format response with sources for transparency
        answer = result["answer"]
        sources = [
            doc.metadata.get("policy_type", "unknown")
            for doc in result["sources"]
        ]
        unique_sources = list(set(sources))
        
        return (
            f"{answer}\n\n"
            f"[Based on: {', '.join(unique_sources)} policies]"
        )
    
    return Tool(
        name="search_policy",
        description=(
            "Search company policies to answer customer questions about "
            "refunds, shipping, returns, warranties, or other policy-related "
            "inquiries. Use this tool when customers ask about company policies, "
            "procedures, or terms and conditions."
        ),
        parameters=PolicySearchParams,
        fn=search_policies,
    )


# ============================================================================
# Agent Setup and Execution
# ============================================================================

async def main():
    """Create and run the policy support agent."""
    
    # Check for API key (optional - will use mock if not provided)
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("⚠️  OPENAI_API_KEY not set. Using mock model for demonstration.")
        print("   Set OPENAI_API_KEY environment variable to use real OpenAI model.\n")
        
        # Use mock model for demonstration
        class MockChatModel(ChatModel):
            """Mock chat model for demonstration."""
            
            def __init__(self):
                self.response_content = "I'll help you with that policy question."
            
            async def chat(
                self, messages: list[Message], options=None
            ) -> Response:
                """Return mock response."""
                # Extract user message to generate context-aware response
                user_msg = next(
                    (msg.content for msg in messages if msg.role == "user"),
                    ""
                )
                
                if "refund" in user_msg.lower():
                    content = (
                        "According to our refund policy, customers can request "
                        "refunds within 30 days of purchase for physical products. "
                        "Refunds are processed within 5-7 business days."
                    )
                elif "shipping" in user_msg.lower():
                    content = (
                        "Our standard shipping takes 5-7 business days and costs $5.99. "
                        "We offer free shipping on orders over $50. Express shipping "
                        "is available for faster delivery."
                    )
                elif "return" in user_msg.lower():
                    content = (
                        "Items can be returned within 14 days of delivery in original "
                        "condition. The customer is responsible for return shipping "
                        "unless the item is defective."
                    )
                else:
                    content = (
                        "I found relevant policy information. Let me provide you with "
                        "the details based on our company policies."
                    )
                
                return Response(
                    content=content,
                    usage=Usage(input_tokens=50, output_tokens=30),
                )
            
            async def stream(self, messages, options=None):
                raise NotImplementedError
            
            def model_info(self) -> ModelInfo:
                return ModelInfo(
                    provider="mock",
                    model="mock-model",
                    capabilities=Capabilities(),
                )
        
        model = MockChatModel()
    else:
        # Use real OpenAI model
        model = OpenAIModel(api_key=api_key, model="gpt-4")
    
    # Set up RAG system
    print("Setting up RAG system...")
    retriever = await setup_rag_system(use_real_embeddings=False)
    
    # Create policy tool
    print("Creating policy search tool...")
    policy_tool = await create_policy_tool(model, retriever)
    
    # Create agent with policy tool
    print("Creating agent...\n")
    agent = make_agent(
        model=model,
        tools=[policy_tool],
        system_message=(
            "You are a helpful and professional customer support agent. "
            "When customers ask about company policies (refunds, shipping, "
            "returns, warranties, etc.), use the search_policy tool to find "
            "accurate and up-to-date information. Always be polite, clear, "
            "and helpful. If you cannot find the answer in the policies, "
            "offer to connect the customer with a human agent."
        ),
        max_iterations=5,
    )
    
    # Example customer queries
    print("=" * 70)
    print("POLICY SUPPORT AGENT - Example Conversations")
    print("=" * 70)
    
    queries = [
        "What's your refund policy?",
        "How long does shipping take?",
        "Can I return a digital product if I don't like it?",
        "What's covered under warranty?",
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n[Example {i}]")
        print(f"Customer: {query}")
        print("-" * 70)
        
        result = await agent.ainvoke(query)
        response = result.response.extract_content()
        
        print(f"Agent: {response}")
        print(f"\n(Tool calls made: {len(result.tool_calls_made)})")
        
        if result.tool_calls_made:
            print("Tools used:")
            for tool_call in result.tool_calls_made:
                print(f"  - {tool_call.function.name}")
        
        print("=" * 70)
    
    print("\n✓ Example completed!")


# ============================================================================
# Run Example
# ============================================================================

if __name__ == "__main__":
    asyncio.run(main())
