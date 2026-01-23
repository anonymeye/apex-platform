"""Knowledge ingestion & processing service."""

import logging
import re
from typing import Optional
from uuid import UUID

from conduit.rag import Document, RecursiveSplitter

from apex.ml.rag.embeddings import EmbeddingService
from apex.ml.rag.retriever import KnowledgeBaseRetriever
from apex.repositories.knowledge_repository import (
    DocumentRepository,
    KnowledgeBaseRepository,
)
from apex.services.rag_tool_service import RAGToolService
from apex.storage.vector_store import ApexVectorStore

logger = logging.getLogger(__name__)


class KnowledgeService:
    """Service for managing knowledge bases and documents."""

    def __init__(
        self,
        knowledge_base_repo: KnowledgeBaseRepository,
        document_repo: DocumentRepository,
        vector_store: ApexVectorStore,
        embedding_service: EmbeddingService,
        chat_model,
    ):
        """Initialize knowledge service.

        Args:
            knowledge_base_repo: Knowledge base repository
            document_repo: Document repository
            vector_store: Vector store instance
            embedding_service: Embedding service
            chat_model: Chat model for RAG
        """
        self.kb_repo = knowledge_base_repo
        self.doc_repo = document_repo
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.chat_model = chat_model

    def _generate_slug(self, name: str) -> str:
        """Generate URL-friendly slug from name.

        Args:
            name: Knowledge base name

        Returns:
            URL-friendly slug
        """
        slug = name.lower().strip()
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[-\s]+", "-", slug)
        return slug

    async def create_knowledge_base(
        self,
        name: str,
        organization_id: UUID,
        description: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> "KnowledgeBase":
        """Create a new knowledge base.

        Args:
            name: Knowledge base name
            organization_id: Organization ID
            description: Optional description
            metadata: Optional metadata

        Returns:
            Created knowledge base
        """
        slug = self._generate_slug(name)

        # Check if slug already exists
        existing = await self.kb_repo.get_by_slug(slug, organization_id)
        if existing:
            # Append number to make unique
            counter = 1
            while existing:
                new_slug = f"{slug}-{counter}"
                existing = await self.kb_repo.get_by_slug(new_slug, organization_id)
                if not existing:
                    slug = new_slug
                    break
                counter += 1

        kb = await self.kb_repo.create(
            name=name,
            slug=slug,
            description=description,
            organization_id=organization_id,
            meta_data=metadata or {},
        )

        logger.info(f"Created knowledge base: {name} (id: {kb.id})")
        return kb

    async def upload_documents(
        self,
        knowledge_base_id: UUID,
        documents: list[dict],  # List of {content, source, metadata}
        auto_create_tool: bool = True,
        auto_add_to_agent_id: Optional[UUID] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> tuple[list["Document"], Optional["Tool"]]:
        """Upload documents to knowledge base and optionally auto-create RAG tool.

        Args:
            knowledge_base_id: Knowledge base ID
            documents: List of document dictionaries with content, source, metadata
            auto_create_tool: Whether to auto-create RAG tool (default: True)
            auto_add_to_agent_id: Optional agent ID to auto-add tool to
            chunk_size: Chunk size for text splitting
            chunk_overlap: Chunk overlap for text splitting

        Returns:
            Tuple of (created documents, created tool if auto_create_tool=True)
        """
        # Get knowledge base
        kb = await self.kb_repo.get(knowledge_base_id)
        if not kb:
            raise ValueError(f"Knowledge base {knowledge_base_id} not found")

        # Split documents into chunks
        splitter = RecursiveSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        all_chunks = []
        for doc_data in documents:
            content = doc_data.get("content", "")
            source = doc_data.get("source", "unknown")
            metadata = doc_data.get("metadata", {})

            # Split into chunks
            chunks = splitter.split_text(content)
            for i, chunk in enumerate(chunks):
                all_chunks.append(
                    {
                        "content": chunk,
                        "source": source,
                        "chunk_index": i,
                        "metadata": {**metadata, "source": source},
                    }
                )

        logger.info(
            f"Split {len(documents)} documents into {len(all_chunks)} chunks for KB {kb.name}"
        )

        # Generate embeddings
        texts = [chunk["content"] for chunk in all_chunks]
        embeddings = await self.embedding_service.embed_documents(texts)

        # Create Document objects for vector store
        vector_docs = []
        for chunk, embedding in zip(all_chunks, embeddings):
            vector_docs.append(
                Document(
                    content=chunk["content"],
                    metadata={
                        **chunk["metadata"],
                        "knowledge_base_id": str(knowledge_base_id),
                        "chunk_index": chunk["chunk_index"],
                    },
                )
            )

        # Add to vector store
        vector_ids = await self.vector_store.add_documents(
            vector_docs, embeddings, knowledge_base_id=knowledge_base_id
        )

        # Save documents to database
        db_documents = []
        for chunk, vector_id in zip(all_chunks, vector_ids):
            db_documents.append(
                {
                    "knowledge_base_id": knowledge_base_id,
                    "content": chunk["content"],
                    "source": chunk["source"],
                    "chunk_index": chunk["chunk_index"],
                    "vector_id": vector_id,
                    "meta_data": chunk["metadata"],  # chunk["metadata"] is from input, stored as meta_data in DB
                }
            )

        created_docs = await self.doc_repo.create_batch(db_documents)

        logger.info(
            f"Uploaded {len(created_docs)} document chunks to knowledge base {kb.name}"
        )

        # Auto-create RAG tool if requested
        created_tool = None
        if auto_create_tool:
            # Check if tool already exists for this KB
            from apex.repositories.tool_repository import ToolRepository

            tool_repo = ToolRepository(self.kb_repo.session)
            existing_tools = await tool_repo.get_by_knowledge_base(knowledge_base_id)

            if not existing_tools:
                # Create retriever for this knowledge base
                retriever = KnowledgeBaseRetriever(
                    vector_store=self.vector_store,
                    embedding_model=self.embedding_service.embedding_model,
                    knowledge_base_id=knowledge_base_id,
                )

                # Create RAG tool service
                rag_tool_service = RAGToolService(
                    tool_repository=tool_repo,
                    vector_retriever=retriever,
                    chat_model=self.chat_model,
                )

                # Auto-create tool
                created_tool = await rag_tool_service.auto_create_rag_tool(
                    knowledge_base_id=knowledge_base_id,
                    knowledge_base_name=kb.name,
                    organization_id=kb.organization_id,
                    auto_add_to_agent_id=auto_add_to_agent_id,
                )

                logger.info(
                    f"Auto-created RAG tool '{created_tool.name}' for knowledge base {kb.name}"
                )
            else:
                logger.info(
                    f"Tool already exists for knowledge base {kb.name}, skipping auto-creation"
                )

        return created_docs, created_tool
