"""Agent repository."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apex.models.agent import Agent
from apex.models.model_ref import ModelRef
from apex.models.tool import AgentTool
from apex.repositories.base import BaseRepository


class AgentRepository(BaseRepository[Agent]):
    """Repository for agents."""

    def __init__(self, session: AsyncSession):
        """Initialize repository."""
        super().__init__(Agent, session)

    async def get_with_tools(self, id: UUID) -> Optional[Agent]:
        """Get agent with tools loaded.

        Args:
            id: Agent ID

        Returns:
            Agent with tools or None
        """
        result = await self.session.execute(
            select(Agent)
            .where(Agent.id == id)
            .options(selectinload(Agent.model_ref).selectinload(ModelRef.connection))
            .options(selectinload(Agent.agent_tools).selectinload(AgentTool.tool))
        )
        return result.scalar_one_or_none()

    async def get_by_organization(
        self, organization_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[Agent]:
        """Get all agents for an organization.

        Args:
            organization_id: Organization ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of agents
        """
        result = await self.session.execute(
            select(Agent)
            .where(Agent.organization_id == organization_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
