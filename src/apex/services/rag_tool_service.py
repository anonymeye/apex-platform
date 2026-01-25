"""Service for creating and managing RAG tools."""

import logging
import re
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

    def _generate_tool_name(self, kb_name: str, organization_id: UUID) -> str:
        """Generate unique tool name from knowledge base name.

        Args:
            kb_name: Knowledge base name
            organization_id: Organization ID for uniqueness

        Returns:
            Generated tool name (e.g., "search_product_docs")
        """
        # Convert to slug
        slug = kb_name.lower().replace(" ", "_").replace("-", "_")
        # Remove special chars
        slug = re.sub(r"[^a-z0-9_]", "", slug)
        base_name = f"search_{slug}"

        # Ensure uniqueness by checking if name exists
        # In production, you'd check the database, but for now we'll use base name
        return base_name

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

    async def auto_create_rag_tool(
        self,
        knowledge_base_id: UUID,
        knowledge_base_name: str,
        organization_id: UUID,
        rag_template: Optional[str] = None,
        rag_k: int = 5,
        auto_add_to_agent_id: Optional[UUID] = None,
    ) -> ToolModel:
        """Auto-create a RAG tool when knowledge base is created.

        Args:
            knowledge_base_id: ID of the knowledge base
            knowledge_base_name: Name of the knowledge base (for tool naming)
            organization_id: Organization ID
            rag_template: Optional custom RAG template
            rag_k: Number of chunks to retrieve (default: 5)
            auto_add_to_agent_id: Optional agent to auto-add tool to

        Returns:
            Created Tool database model
        """
        # Generate tool name
        tool_name = self._generate_tool_name(knowledge_base_name, organization_id)

        # Check if tool with this name already exists
        existing_tool = await self.tool_repository.get_by_name(
            tool_name, organization_id
        )
        if existing_tool:
            logger.warning(
                f"Tool with name '{tool_name}' already exists. Returning existing tool."
            )
            return existing_tool

        # Use default template if not provided
        template = rag_template or self._get_default_rag_template()

        # Create tool description
        tool_description = (
            f"Search the {knowledge_base_name} knowledge base for information. "
            f"Use this tool when you need to find information from the uploaded documents."
        )

        # Save tool to database
        tool_model = await self.tool_repository.create(
            name=tool_name,
            description=tool_description,
            tool_type="rag",
            knowledge_base_id=knowledge_base_id,
            organization_id=organization_id,
            config={
                "tool_name": tool_name,
                "rag_template": template,
                "rag_k": rag_k,
            },
            rag_template=template,
            rag_k=rag_k,
            auto_created=True,
        )

        logger.info(
            f"Auto-created RAG tool '{tool_name}' for knowledge base '{knowledge_base_name}'"
        )

        # Auto-add to agent if specified
        if auto_add_to_agent_id:
            from apex.repositories.tool_repository import AgentToolRepository

            agent_tool_repo = AgentToolRepository(self.tool_repository.session)
            await agent_tool_repo.add_tool_to_agent(
                auto_add_to_agent_id, tool_model.id
            )
            logger.info(f"Auto-added tool '{tool_name}' to agent {auto_add_to_agent_id}")

        return tool_model

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

        # Recreate RAG chain from stored config
        template = tool_model.rag_template or self._get_default_rag_template()
        k = tool_model.rag_k or 5
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
