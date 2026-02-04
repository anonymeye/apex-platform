"""Knowledge repository."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apex.models.knowledge import Document, KnowledgeBase
from apex.repositories.base import BaseRepository


class KnowledgeBaseRepository(BaseRepository[KnowledgeBase]):
    """Repository for knowledge bases."""

    def __init__(self, session: AsyncSession):
        """Initialize repository."""
        super().__init__(KnowledgeBase, session)

    async def get_by_slug(
        self, slug: str, organization_id: UUID
    ) -> Optional[KnowledgeBase]:
        """Get knowledge base by slug and organization.

        Args:
            slug: Knowledge base slug
            organization_id: Organization ID

        Returns:
            Knowledge base or None
        """
        result = await self.session.execute(
            select(KnowledgeBase)
            .where(
                KnowledgeBase.slug == slug,
                KnowledgeBase.organization_id == organization_id,
            )
            .options(selectinload(KnowledgeBase.documents))
        )
        return result.scalar_one_or_none()

    async def get_by_organization(
        self, organization_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[KnowledgeBase]:
        """Get all knowledge bases for an organization.

        Args:
            organization_id: Organization ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of knowledge bases
        """
        result = await self.session.execute(
            select(KnowledgeBase)
            .where(KnowledgeBase.organization_id == organization_id)
            .offset(skip)
            .limit(limit)
            .options(selectinload(KnowledgeBase.documents))
        )
        return list(result.scalars().all())


class DocumentRepository(BaseRepository[Document]):
    """Repository for documents."""

    def __init__(self, session: AsyncSession):
        """Initialize repository."""
        super().__init__(Document, session)

    async def get_by_knowledge_base(
        self, knowledge_base_id: UUID, skip: int = 0, limit: int = 1000
    ) -> list[Document]:
        """Get all documents for a knowledge base.

        Args:
            knowledge_base_id: Knowledge base ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of documents
        """
        result = await self.session.execute(
            select(Document)
            .where(Document.knowledge_base_id == knowledge_base_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create_batch(self, documents: list[dict]) -> list[Document]:
        """Create multiple documents in batch.

        Args:
            documents: List of document dictionaries

        Returns:
            List of created document instances
        """
        instances = [Document(**doc) for doc in documents]
        self.session.add_all(instances)
        await self.session.flush()
        for instance in instances:
            await self.session.refresh(instance)
        return instances
