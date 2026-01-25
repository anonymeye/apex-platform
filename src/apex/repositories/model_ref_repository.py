"""Model reference repository."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apex.models.model_ref import ModelRef
from apex.repositories.base import BaseRepository


class ModelRefRepository(BaseRepository[ModelRef]):
    """Repository for model references."""

    def __init__(self, session: AsyncSession):
        super().__init__(ModelRef, session)

    async def get_by_organization(
        self, organization_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[ModelRef]:
        result = await self.session.execute(
            select(ModelRef)
            .where(ModelRef.organization_id == organization_id)
            .options(selectinload(ModelRef.connection))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_for_org(self, id: UUID, organization_id: UUID) -> Optional[ModelRef]:
        result = await self.session.execute(
            select(ModelRef)
            .where(
                ModelRef.id == id,
                ModelRef.organization_id == organization_id,
            )
            .options(selectinload(ModelRef.connection))
        )
        return result.scalar_one_or_none()

