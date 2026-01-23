"""Agent lifecycle management service."""

import logging
from typing import Optional
from uuid import UUID

from apex.models.agent import Agent
from apex.repositories.agent_repository import AgentRepository
from apex.repositories.tool_repository import AgentToolRepository, ToolRepository

logger = logging.getLogger(__name__)


class AgentService:
    """Service for managing agents."""

    def __init__(
        self,
        agent_repo: AgentRepository,
        tool_repo: ToolRepository,
        agent_tool_repo: AgentToolRepository,
    ):
        """Initialize agent service.

        Args:
            agent_repo: Agent repository
            tool_repo: Tool repository
            agent_tool_repo: AgentTool repository
        """
        self.agent_repo = agent_repo
        self.tool_repo = tool_repo
        self.agent_tool_repo = agent_tool_repo

    async def create_agent(
        self,
        name: str,
        organization_id: UUID,
        model_provider: str,
        model_name: str,
        description: Optional[str] = None,
        system_message: Optional[str] = None,
        max_iterations: int = 10,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        config: Optional[dict] = None,
        tool_ids: Optional[list[UUID]] = None,
    ) -> Agent:
        """Create a new agent.

        Args:
            name: Agent name
            organization_id: Organization ID
            model_provider: Model provider (e.g., 'openai', 'anthropic')
            model_name: Model name (e.g., 'gpt-4', 'claude-3-opus')
            description: Optional description
            system_message: Optional system message
            max_iterations: Maximum tool-calling iterations
            temperature: Model temperature
            max_tokens: Maximum tokens in response
            config: Additional configuration
            tool_ids: List of tool IDs to attach

        Returns:
            Created agent

        Raises:
            ValueError: If tool IDs are invalid or don't belong to organization
        """
        # Validate tool IDs if provided
        if tool_ids:
            for tool_id in tool_ids:
                tool = await self.tool_repo.get(tool_id)
                if not tool:
                    raise ValueError(f"Tool {tool_id} not found")
                if tool.organization_id != organization_id:
                    raise ValueError(
                        f"Tool {tool_id} does not belong to organization {organization_id}"
                    )

        # Create agent
        agent = await self.agent_repo.create(
            name=name,
            description=description,
            model_provider=model_provider,
            model_name=model_name,
            system_message=system_message,
            max_iterations=max_iterations,
            temperature=temperature,
            max_tokens=max_tokens,
            config=config or {},
            organization_id=organization_id,
        )

        logger.info(f"Created agent: {name} (id: {agent.id})")

        # Attach tools if provided
        if tool_ids:
            for tool_id in tool_ids:
                await self.agent_tool_repo.add_tool_to_agent(agent.id, tool_id)
            logger.info(f"Attached {len(tool_ids)} tools to agent {agent.id}")

        return agent

    async def get_agent(self, agent_id: UUID, organization_id: UUID) -> Optional[Agent]:
        """Get an agent by ID.

        Args:
            agent_id: Agent ID
            organization_id: Organization ID (for authorization)

        Returns:
            Agent if found and belongs to organization, None otherwise
        """
        agent = await self.agent_repo.get(agent_id)
        if agent and agent.organization_id == organization_id:
            return await self.agent_repo.get_with_tools(agent_id)
        return None

    async def list_agents(
        self, organization_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[Agent]:
        """List agents for an organization.

        Args:
            organization_id: Organization ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of agents
        """
        return await self.agent_repo.get_by_organization(organization_id, skip=skip, limit=limit)

    async def update_agent(
        self,
        agent_id: UUID,
        organization_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        model_provider: Optional[str] = None,
        model_name: Optional[str] = None,
        system_message: Optional[str] = None,
        max_iterations: Optional[int] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        config: Optional[dict] = None,
        tool_ids: Optional[list[UUID]] = None,
    ) -> Optional[Agent]:
        """Update an agent.

        Args:
            agent_id: Agent ID
            organization_id: Organization ID (for authorization)
            name: New name
            description: New description
            model_provider: New model provider
            model_name: New model name
            system_message: New system message
            max_iterations: New max iterations
            temperature: New temperature
            max_tokens: New max tokens
            config: New config (will merge with existing)
            tool_ids: New tool IDs (will replace existing tools)

        Returns:
            Updated agent or None if not found/unauthorized

        Raises:
            ValueError: If tool IDs are invalid
        """
        agent = await self.agent_repo.get(agent_id)
        if not agent or agent.organization_id != organization_id:
            return None

        # Validate tool IDs if provided
        if tool_ids is not None:
            for tool_id in tool_ids:
                tool = await self.tool_repo.get(tool_id)
                if not tool:
                    raise ValueError(f"Tool {tool_id} not found")
                if tool.organization_id != organization_id:
                    raise ValueError(
                        f"Tool {tool_id} does not belong to organization {organization_id}"
                    )

        # Build update dict
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        if model_provider is not None:
            update_data["model_provider"] = model_provider
        if model_name is not None:
            update_data["model_name"] = model_name
        if system_message is not None:
            update_data["system_message"] = system_message
        if max_iterations is not None:
            update_data["max_iterations"] = max_iterations
        if temperature is not None:
            update_data["temperature"] = temperature
        if max_tokens is not None:
            update_data["max_tokens"] = max_tokens
        if config is not None:
            # Merge with existing config
            existing_config = agent.config or {}
            update_data["config"] = {**existing_config, **config}

        # Update agent
        if update_data:
            agent = await self.agent_repo.update(agent_id, **update_data)
            logger.info(f"Updated agent {agent_id}")

        # Update tools if provided
        if tool_ids is not None:
            # Remove existing tools
            existing_agent_tools = await self.agent_tool_repo.get_by_agent(agent_id)
            for agent_tool in existing_agent_tools:
                await self.agent_tool_repo.delete(agent_tool.id)

            # Add new tools
            for tool_id in tool_ids:
                await self.agent_tool_repo.add_tool_to_agent(agent_id, tool_id)
            logger.info(f"Updated tools for agent {agent_id}: {len(tool_ids)} tools")

        return await self.agent_repo.get_with_tools(agent_id)

    async def delete_agent(self, agent_id: UUID, organization_id: UUID) -> bool:
        """Delete an agent.

        Args:
            agent_id: Agent ID
            organization_id: Organization ID (for authorization)

        Returns:
            True if deleted, False if not found/unauthorized
        """
        agent = await self.agent_repo.get(agent_id)
        if not agent or agent.organization_id != organization_id:
            return False

        await self.agent_repo.delete(agent_id)
        logger.info(f"Deleted agent {agent_id}")
        return True
