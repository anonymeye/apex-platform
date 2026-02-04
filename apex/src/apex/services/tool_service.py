"""Tool lifecycle service (top-level tools API)."""

import logging
from typing import Optional
from uuid import UUID

from apex.models.tool import Tool
from apex.repositories.knowledge_repository import KnowledgeBaseRepository
from apex.repositories.tool_repository import ToolRepository

logger = logging.getLogger(__name__)


class ToolService:
    """Service for managing tools at org level (list, get, create, update, delete)."""

    def __init__(
        self,
        tool_repo: ToolRepository,
        knowledge_base_repo: KnowledgeBaseRepository,
    ):
        """Initialize tool service.

        Args:
            tool_repo: Tool repository
            knowledge_base_repo: Knowledge base repository (for validating knowledge_base_id on create)
        """
        self.tool_repo = tool_repo
        self.knowledge_base_repo = knowledge_base_repo

    async def list_tools(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Tool]:
        """List all tools for an organization.

        Args:
            organization_id: Organization ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of tools
        """
        return await self.tool_repo.get_by_organization(
            organization_id=organization_id,
            skip=skip,
            limit=limit,
        )

    async def get_tool(
        self,
        tool_id: UUID,
        organization_id: UUID,
    ) -> Optional[Tool]:
        """Get a tool by ID if it belongs to the organization.

        Args:
            tool_id: Tool ID
            organization_id: Organization ID (for authorization)

        Returns:
            Tool if found and belongs to org, None otherwise
        """
        tool = await self.tool_repo.get(tool_id)
        if tool and tool.organization_id == organization_id:
            return tool
        return None

    async def create_tool(
        self,
        organization_id: UUID,
        name: str,
        description: str,
        tool_type: str,
        knowledge_base_id: Optional[UUID] = None,
        config: Optional[dict] = None,
    ) -> Tool:
        """Create a new tool.

        Args:
            organization_id: Organization ID
            name: Tool name (must be unique)
            description: Tool description
            tool_type: Tool type (rag, api, function, etc.)
            knowledge_base_id: Optional knowledge base ID (must belong to org if provided)
            config: Optional type-specific config

        Returns:
            Created tool

        Raises:
            ValueError: If name already exists or knowledge_base_id is invalid
        """
        existing = await self.tool_repo.get_by_name(name, organization_id)
        if existing:
            raise ValueError(f"Tool with name '{name}' already exists")

        if knowledge_base_id is not None:
            kb = await self.knowledge_base_repo.get(knowledge_base_id)
            if not kb or kb.organization_id != organization_id:
                raise ValueError("Knowledge base not found or does not belong to organization")

        tool = await self.tool_repo.create(
            name=name,
            description=description,
            tool_type=tool_type,
            knowledge_base_id=knowledge_base_id,
            config=config or {},
            organization_id=organization_id,
        )
        logger.info(f"Created tool: {name} (id={tool.id})")
        return tool

    async def update_tool(
        self,
        tool_id: UUID,
        organization_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        config: Optional[dict] = None,
    ) -> Optional[Tool]:
        """Update a tool.

        Args:
            tool_id: Tool ID
            organization_id: Organization ID (for authorization)
            name: Optional new name (must remain unique)
            description: Optional new description
            config: Optional config (merged with existing)

        Returns:
            Updated tool if found and belongs to org, None otherwise
        """
        tool = await self.get_tool(tool_id, organization_id)
        if not tool:
            return None

        update_data: dict = {}
        if name is not None:
            if name != tool.name:
                existing = await self.tool_repo.get_by_name(name, organization_id)
                if existing:
                    raise ValueError(f"Tool with name '{name}' already exists")
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        if config is not None:
            existing_config = tool.config or {}
            update_data["config"] = {**existing_config, **config}

        if not update_data:
            return tool

        updated = await self.tool_repo.update(tool_id, update_data)
        return updated

    async def delete_tool(
        self,
        tool_id: UUID,
        organization_id: UUID,
    ) -> bool:
        """Delete a tool (and its agent associations via cascade).

        Args:
            tool_id: Tool ID
            organization_id: Organization ID (for authorization)

        Returns:
            True if deleted, False if not found or wrong org
        """
        tool = await self.get_tool(tool_id, organization_id)
        if not tool:
            return False
        await self.tool_repo.delete(tool_id)
        logger.info(f"Deleted tool: {tool.name} (id={tool_id})")
        return True
