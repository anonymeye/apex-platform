"""Agent CRUD endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apex.api.dependencies import get_current_user_from_token
from apex.api.v1.schemas.agents import AgentCreate, AgentResponse, AgentUpdate, ToolInfo
from apex.core.database import get_db
from apex.repositories.agent_repository import AgentRepository
from apex.repositories.model_ref_repository import ModelRefRepository
from apex.repositories.tool_repository import AgentToolRepository, ToolRepository
from apex.services.agent_service import AgentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])

# Debug: Log router creation
logger.info("Agent router initialized")


def get_agent_service(db: AsyncSession = Depends(get_db)) -> AgentService:
    """Get agent service instance."""
    return AgentService(
        agent_repo=AgentRepository(db),
        tool_repo=ToolRepository(db),
        agent_tool_repo=AgentToolRepository(db),
        model_ref_repo=ModelRefRepository(db),
    )


def _agent_to_response(agent) -> AgentResponse:
    """Convert Agent model to AgentResponse schema."""
    return AgentResponse(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        model_ref_id=agent.model_ref_id,
        model_ref=(
            {
                "id": agent.model_ref.id,
                "name": agent.model_ref.name,
                "runtime_id": agent.model_ref.runtime_id,
                "connection": {
                    "id": agent.model_ref.connection.id,
                    "name": agent.model_ref.connection.name,
                    "provider": agent.model_ref.connection.provider,
                    "connection_type": agent.model_ref.connection.connection_type,
                },
            }
            if getattr(agent, "model_ref", None) and getattr(agent.model_ref, "connection", None)
            else None
        ),
        system_message=agent.system_message,
        max_iterations=agent.max_iterations,
        temperature=agent.temperature,
        max_tokens=agent.max_tokens,
        config=agent.config,
        organization_id=agent.organization_id,
        tools=[
            ToolInfo(
                id=agent_tool.tool.id,
                name=agent_tool.tool.name,
                description=agent_tool.tool.description,
                tool_type=agent_tool.tool.tool_type,
            )
            for agent_tool in agent.agent_tools
        ],
        created_at=agent.created_at.isoformat(),
        updated_at=agent.updated_at.isoformat(),
    )


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: AgentCreate,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_current_user_from_token),
    agent_service: AgentService = Depends(get_agent_service),
):
    """Create a new agent.

    Args:
        agent_data: Agent creation data
        db: Database session
        user_data: Current user data from token
        agent_service: Agent service instance

    Returns:
        Created agent

    Raises:
        HTTPException: If validation fails or tool IDs are invalid
    """
    logger.info(
        f"Creating agent with data: name={agent_data.name}, model_ref_id={agent_data.model_ref_id}"
    )
    organization_id = UUID(user_data.get("org_id"))

    try:
        agent = await agent_service.create_agent(
            name=agent_data.name,
            organization_id=organization_id,
            model_ref_id=agent_data.model_ref_id,
            description=agent_data.description,
            system_message=agent_data.system_message,
            max_iterations=agent_data.max_iterations,
            temperature=agent_data.temperature,
            max_tokens=agent_data.max_tokens,
            config=agent_data.config,
            tool_ids=agent_data.tool_ids,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Reload with tools
    agent = await agent_service.get_agent(agent.id, organization_id)
    return _agent_to_response(agent)


@router.get("", response_model=list[AgentResponse])
async def list_agents(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_current_user_from_token),
    agent_service: AgentService = Depends(get_agent_service),
):
    """List all agents for the organization.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        user_data: Current user data from token
        agent_service: Agent service instance

    Returns:
        List of agents
    """
    organization_id = UUID(user_data.get("org_id"))

    agents = await agent_service.list_agents(organization_id, skip=skip, limit=limit)

    # Load tools for each agent
    result = []
    for agent in agents:
        agent_with_tools = await agent_service.get_agent(agent.id, organization_id)
        if agent_with_tools:
            result.append(_agent_to_response(agent_with_tools))

    return result


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_current_user_from_token),
    agent_service: AgentService = Depends(get_agent_service),
):
    """Get an agent by ID.

    Args:
        agent_id: Agent ID
        db: Database session
        user_data: Current user data from token
        agent_service: Agent service instance

    Returns:
        Agent details

    Raises:
        HTTPException: If agent not found or unauthorized
    """
    organization_id = UUID(user_data.get("org_id"))

    agent = await agent_service.get_agent(agent_id, organization_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        )

    return _agent_to_response(agent)


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: UUID,
    agent_data: AgentUpdate,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_current_user_from_token),
    agent_service: AgentService = Depends(get_agent_service),
):
    """Update an agent.

    Args:
        agent_id: Agent ID
        agent_data: Agent update data
        db: Database session
        user_data: Current user data from token
        agent_service: Agent service instance

    Returns:
        Updated agent

    Raises:
        HTTPException: If agent not found, unauthorized, or validation fails
    """
    organization_id = UUID(user_data.get("org_id"))

    try:
        agent = await agent_service.update_agent(
            agent_id=agent_id,
            organization_id=organization_id,
            name=agent_data.name,
            description=agent_data.description,
            model_ref_id=agent_data.model_ref_id,
            system_message=agent_data.system_message,
            max_iterations=agent_data.max_iterations,
            temperature=agent_data.temperature,
            max_tokens=agent_data.max_tokens,
            config=agent_data.config,
            tool_ids=agent_data.tool_ids,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        )

    return _agent_to_response(agent)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_current_user_from_token),
    agent_service: AgentService = Depends(get_agent_service),
):
    """Delete an agent.

    Args:
        agent_id: Agent ID
        db: Database session
        user_data: Current user data from token
        agent_service: Agent service instance

    Raises:
        HTTPException: If agent not found or unauthorized
    """
    organization_id = UUID(user_data.get("org_id"))

    deleted = await agent_service.delete_agent(agent_id, organization_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        )
