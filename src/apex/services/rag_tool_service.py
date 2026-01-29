"""Service for creating and managing RAG tools."""

import logging
from typing import Optional
from uuid import UUID

from conduit.rag import RAGChain, VectorRetriever
from conduit.tools import Tool
from pydantic import BaseModel, Field

from apex.ml.rag.retriever import KnowledgeBaseRetriever
from apex.ml.rag.embeddings import EmbeddingService
from apex.storage.vector_store import ApexVectorStore
from apex.models.tool import Tool as ToolModel
from apex.repositories.tool_repository import ToolRepository

logger = logging.getLogger(__name__)


class KnowledgeBaseSearchParams(BaseModel):
    """Parameters for knowledge base search tool."""

    query: str = Field(description="The question or query to search the knowledge base")


class RAGToolService:
    """Service for creating and managing RAG tools."""

    def __init__(
        self,
        tool_repository: ToolRepository,
        vector_retriever: VectorRetriever | ApexVectorStore,
        chat_model=None,
        embedding_service: EmbeddingService | None = None,
    ):
        """Initialize RAG tool service.

        Args:
            tool_repository: Tool repository instance
            vector_retriever: Retriever (or vector store wrapper) for RAG
            chat_model: Optional ChatModel instance for RAG chain (can be provided at call time)
            embedding_service: Optional embedding service (used to build KB-scoped retrievers at runtime)
        """
        self.tool_repository = tool_repository
        self.vector_retriever = vector_retriever
        self.chat_model = chat_model
        self.embedding_service = embedding_service

    def _get_retriever_for_tool(self, tool_model: ToolModel) -> VectorRetriever:
        """Resolve the correct retriever for a specific tool."""
        # If we were constructed with a KnowledgeBaseRetriever (or any VectorRetriever),
        # just use it as-is.
        if isinstance(self.vector_retriever, VectorRetriever):
            return self.vector_retriever

        # Otherwise we expect an ApexVectorStore and (optionally) an EmbeddingService
        # so we can build a KB-scoped retriever at runtime.
        if isinstance(self.vector_retriever, ApexVectorStore) and self.embedding_service:
            return KnowledgeBaseRetriever(
                vector_store=self.vector_retriever,
                embedding_model=self.embedding_service.embedding_model,
                knowledge_base_id=tool_model.knowledge_base_id,
            )

        raise ValueError("RAGToolService is missing a usable retriever configuration")

    def _get_default_rag_template(self) -> str:
        """Get default RAG template.

        Returns:
            Default template string
        """
        return (
            "Use the following information from the knowledge base to answer "
            "the question accurately. If the information is not available, "
            "say so clearly.\n\n"
            "Context:\n{context}\n\n"
            "Question: {question}\n\n"
            "Answer:"
        )

    async def create_rag_tool_function(
        self,
        rag_chain: RAGChain,
        knowledge_base_name: str,
    ):
        """Create the async function for the RAG tool.

        Args:
            rag_chain: RAGChain instance
            knowledge_base_name: Name of knowledge base for source attribution

        Returns:
            Async function that can be used as tool function
        """
        async def search_knowledge_base(params: KnowledgeBaseSearchParams) -> str:
            """Search knowledge base and return answer.

            This function is called by the agent when it decides to use the tool.
            """
            try:
                result = await rag_chain(params.query)

                answer = result["answer"]
                sources = [
                    doc.metadata.get("source", "unknown")
                    for doc in result.get("sources", [])
                ]
                unique_sources = list(set(sources))[:3]  # Show top 3 sources

                source_text = (
                    f"\n\n[Sources: {', '.join(unique_sources)}]"
                    if unique_sources
                    else ""
                )

                return f"{answer}{source_text}"
            except Exception as e:
                logger.error(f"Error in RAG tool execution: {e}")
                return f"I encountered an error while searching the knowledge base: {str(e)}"

        return search_knowledge_base

    async def create_conduit_tool_from_db(self, tool_model: ToolModel, chat_model=None) -> Tool:
        """Create a Conduit Tool instance from database model.

        This is used at runtime to convert stored tool config into executable tool.

        Args:
            tool_model: Tool database model
            chat_model: Optional ChatModel override for generation (defaults to self.chat_model)

        Returns:
            Conduit Tool instance
        """
        if tool_model.tool_type != "rag":
            raise ValueError(f"Tool type '{tool_model.tool_type}' not supported yet")

        model = chat_model or self.chat_model
        if model is None:
            raise ValueError("No chat model provided for RAG tool execution")

        # Recreate RAG chain from stored config (generic Tool stores RAG params in config)
        cfg = tool_model.config or {}
        template = cfg.get("rag_template") or self._get_default_rag_template()
        k = cfg.get("rag_k", 5)
        retriever = self._get_retriever_for_tool(tool_model)

        rag_chain = RAGChain(
            model=model,
            retriever=retriever,
            template=template,
            k=k,
        )

        # Get knowledge base name for source attribution
        kb_name = "knowledge base"
        if tool_model.knowledge_base:
            kb_name = tool_model.knowledge_base.name

        # Create tool function
        tool_function = await self.create_rag_tool_function(rag_chain, kb_name)

        # Create Conduit Tool
        return Tool(
            name=tool_model.name,
            description=tool_model.description,
            parameters=KnowledgeBaseSearchParams,
            fn=tool_function,
        )
