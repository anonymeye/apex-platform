"""Tool repository."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apex.models.tool import AgentTool, Tool
from apex.repositories.base import BaseRepository


class ToolRepository(BaseRepository[Tool]):
    """Repository for tools."""

    def __init__(self, session: AsyncSession):
        """Initialize repository."""
        super().__init__(Tool, session)

    async def get_by_name(
        self, name: str, organization_id: UUID
    ) -> Optional[Tool]:
        """Get tool by name and organization.

        Args:
            name: Tool name
            organization_id: Organization ID

        Returns:
            Tool or None
        """
        result = await self.session.execute(
            select(Tool).where(
                Tool.name == name,
                Tool.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_knowledge_base(
        self, knowledge_base_id: UUID
    ) -> list[Tool]:
        """Get all tools for a knowledge base.

        Args:
            knowledge_base_id: Knowledge base ID

        Returns:
            List of tools
        """
        result = await self.session.execute(
            select(Tool).where(Tool.knowledge_base_id == knowledge_base_id)
        )
        return list(result.scalars().all())

    async def get_by_organization(
        self, organization_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[Tool]:
        """Get all tools for an organization.

        Args:
            organization_id: Organization ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of tools
        """
        result = await self.session.execute(
            select(Tool)
            .where(Tool.organization_id == organization_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())


class AgentToolRepository(BaseRepository[AgentTool]):
    """Repository for agent-tool relationships."""

    def __init__(self, session: AsyncSession):
        """Initialize repository."""
        super().__init__(AgentTool, session)

    async def get_by_agent(self, agent_id: UUID) -> list[AgentTool]:
        """Get all tools for an agent.

        Args:
            agent_id: Agent ID

        Returns:
            List of agent-tool relationships
        """
        result = await self.session.execute(
            select(AgentTool)
            .where(AgentTool.agent_id == agent_id)
            .options(selectinload(AgentTool.tool))
        )
        return list(result.scalars().all())

    async def add_tool_to_agent(
        self, agent_id: UUID, tool_id: UUID, config: Optional[dict] = None
    ) -> AgentTool:
        """Add a tool to an agent.

        Args:
            agent_id: Agent ID
            tool_id: Tool ID
            config: Optional tool-specific configuration

        Returns:
            Created agent-tool relationship
        """
        # Check if relationship already exists
        result = await self.session.execute(
            select(AgentTool).where(
                AgentTool.agent_id == agent_id,
                AgentTool.tool_id == tool_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        # Create new relationship
        return await self.create(
            agent_id=agent_id, tool_id=tool_id, config=config or {}
        )

    async def remove_tool_from_agent(
        self, agent_id: UUID, tool_id: UUID
    ) -> bool:
        """Remove a tool from an agent.

        Args:
            agent_id: Agent ID
            tool_id: Tool ID

        Returns:
            True if removed, False if not found
        """
        result = await self.session.execute(
            select(AgentTool).where(
                AgentTool.agent_id == agent_id,
                AgentTool.tool_id == tool_id,
            )
        )
        agent_tool = result.scalar_one_or_none()
        if agent_tool:
            await self.session.delete(agent_tool)
            await self.session.flush()
            return True
        return False
