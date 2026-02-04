"""Knowledge ingestion & processing service."""

import logging
import re
from typing import Optional
from uuid import UUID

from conduit.rag import Document, RecursiveSplitter

from apex.ml.rag.embeddings import EmbeddingService
from apex.repositories.knowledge_repository import (
    DocumentRepository,
    KnowledgeBaseRepository,
)
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
    ):
        """Initialize knowledge service.

        Args:
            knowledge_base_repo: Knowledge base repository
            document_repo: Document repository
            vector_store: Vector store instance
            embedding_service: Embedding service
        """
        self.kb_repo = knowledge_base_repo
        self.doc_repo = document_repo
        self.vector_store = vector_store
        self.embedding_service = embedding_service

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

    async def update_knowledge_base(
        self,
        knowledge_base_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> "KnowledgeBase":
        """Update a knowledge base.

        Args:
            knowledge_base_id: Knowledge base ID
            name: Optional new name
            description: Optional new description
            metadata: Optional new metadata

        Returns:
            Updated knowledge base
        """
        kb = await self.kb_repo.get(knowledge_base_id)
        if not kb:
            raise ValueError(f"Knowledge base {knowledge_base_id} not found")

        update_data = {}
        if name is not None:
            update_data["name"] = name
            # Regenerate slug if name changed
            update_data["slug"] = self._generate_slug(name)
        if description is not None:
            update_data["description"] = description
        if metadata is not None:
            update_data["meta_data"] = metadata

        if update_data:
            updated_kb = await self.kb_repo.update(knowledge_base_id, update_data)
            logger.info(f"Updated knowledge base: {kb.name} (id: {kb.id})")
            return updated_kb

        return kb

    async def delete_knowledge_base(self, knowledge_base_id: UUID) -> None:
        """Delete a knowledge base and all its documents.

        Args:
            knowledge_base_id: Knowledge base ID
        """
        kb = await self.kb_repo.get(knowledge_base_id)
        if not kb:
            raise ValueError(f"Knowledge base {knowledge_base_id} not found")

        # Delete all documents from vector store
        documents = await self.doc_repo.get_by_knowledge_base(knowledge_base_id)
        if documents:
            vector_ids = [doc.vector_id for doc in documents if doc.vector_id and doc.vector_id.strip()]
            if vector_ids:
                await self.vector_store.delete_documents(vector_ids, knowledge_base_id)

        # Delete documents from database
        for doc in documents:
            await self.doc_repo.delete(doc.id)

        # Delete knowledge base
        await self.kb_repo.delete(knowledge_base_id)

        logger.info(f"Deleted knowledge base: {kb.name} (id: {kb.id})")

    async def delete_document(self, document_id: UUID) -> None:
        """Delete a single document.

        Args:
            document_id: Document ID
        """
        doc = await self.doc_repo.get(document_id)
        if not doc:
            raise ValueError(f"Document {document_id} not found")

        # Delete from vector store if vector_id exists
        if doc.vector_id:
            await self.vector_store.delete_documents([doc.vector_id], doc.knowledge_base_id)

        # Delete from database
        await self.doc_repo.delete(document_id)

        logger.info(f"Deleted document {document_id} from knowledge base {doc.knowledge_base_id}")

    async def upload_documents(
        self,
        knowledge_base_id: UUID,
        documents: list[dict],  # List of {content, source, metadata}
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> list["Document"]:
        """Upload documents to knowledge base.

        Args:
            knowledge_base_id: Knowledge base ID
            documents: List of document dictionaries with content, source, metadata
            chunk_size: Chunk size for text splitting
            chunk_overlap: Chunk overlap for text splitting

        Returns:
            List of created document records
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

            # Split into chunks (split() returns list[Document])
            chunks = splitter.split(content)
            for i, chunk in enumerate(chunks):
                all_chunks.append(
                    {
                        "content": chunk.content,
                        "source": source,
                        "chunk_index": i,
                        "metadata": {**metadata, "source": source, **chunk.metadata},
                    }
                )

        logger.info(
            f"Split {len(documents)} documents into {len(all_chunks)} chunks for KB {kb.name}"
        )

        # Generate embeddings
        texts = [chunk["content"] for chunk in all_chunks]
        embeddings = await self.embedding_service.embed_documents(texts)

        # Create Document objects for vector store (conduit Document.metadata is dict[str, str])
        vector_docs = []
        for chunk, embedding in zip(all_chunks, embeddings):
            raw_meta = {
                **chunk["metadata"],
                "knowledge_base_id": str(knowledge_base_id),
                "chunk_index": str(chunk["chunk_index"]),
            }
            metadata_str = {k: str(v) for k, v in raw_meta.items()}
            vector_docs.append(
                Document(content=chunk["content"], metadata=metadata_str)
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

        return created_docs
