"""Connection repository."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apex.models.connection import Connection
from apex.repositories.base import BaseRepository


class ConnectionRepository(BaseRepository[Connection]):
    """Repository for connections."""

    def __init__(self, session: AsyncSession):
        super().__init__(Connection, session)

    async def get_by_organization(
        self, organization_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[Connection]:
        result = await self.session.execute(
            select(Connection)
            .where(Connection.organization_id == organization_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_for_org(self, id: UUID, organization_id: UUID) -> Optional[Connection]:
        result = await self.session.execute(
            select(Connection).where(
                Connection.id == id,
                Connection.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

