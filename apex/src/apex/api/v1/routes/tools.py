"""Top-level tool CRUD endpoints (org-scoped)."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apex.api.dependencies import get_current_user_from_token
from apex.api.v1.schemas.tools import ToolCreate, ToolResponse, ToolUpdate
from apex.core.database import get_db
from apex.repositories.knowledge_repository import KnowledgeBaseRepository
from apex.repositories.tool_repository import ToolRepository
from apex.services.tool_service import ToolService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tools", tags=["tools"])


def get_tool_service(db: AsyncSession = Depends(get_db)) -> ToolService:
    """Get tool service instance."""
    return ToolService(
        tool_repo=ToolRepository(db),
        knowledge_base_repo=KnowledgeBaseRepository(db),
    )


def _tool_to_response(tool) -> ToolResponse:
    """Convert Tool model to ToolResponse schema."""
    return ToolResponse(
        id=tool.id,
        name=tool.name,
        description=tool.description,
        tool_type=tool.tool_type,
        knowledge_base_id=tool.knowledge_base_id,
        config=tool.config,
        organization_id=tool.organization_id,
        created_at=tool.created_at.isoformat(),
        updated_at=tool.updated_at.isoformat(),
    )


@router.get("", response_model=list[ToolResponse])
async def list_tools(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_current_user_from_token),
    tool_service: ToolService = Depends(get_tool_service),
):
    """List all tools for the current organization.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return (default 100)
        db: Database session
        user_data: Current user data from token
        tool_service: Tool service instance

    Returns:
        List of tools
    """
    organization_id = UUID(user_data.get("org_id"))
    tools = await tool_service.list_tools(organization_id=organization_id, skip=skip, limit=limit)
    return [_tool_to_response(t) for t in tools]


@router.get("/{tool_id}", response_model=ToolResponse)
async def get_tool(
    tool_id: UUID,
    user_data: dict = Depends(get_current_user_from_token),
    tool_service: ToolService = Depends(get_tool_service),
):
    """Get a single tool by ID.

    Args:
        tool_id: Tool ID
        user_data: Current user data from token
        tool_service: Tool service instance

    Returns:
        Tool if found and belongs to org

    Raises:
        HTTPException: If tool not found or unauthorized
    """
    organization_id = UUID(user_data.get("org_id"))
    tool = await tool_service.get_tool(tool_id=tool_id, organization_id=organization_id)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found",
        )
    return _tool_to_response(tool)


@router.post("", response_model=ToolResponse, status_code=status.HTTP_201_CREATED)
async def create_tool(
    tool_data: ToolCreate,
    user_data: dict = Depends(get_current_user_from_token),
    tool_service: ToolService = Depends(get_tool_service),
):
    """Create a new tool (standalone or linked to a knowledge base).

    Args:
        tool_data: Tool create payload
        user_data: Current user data from token
        tool_service: Tool service instance

    Returns:
        Created tool

    Raises:
        HTTPException: If validation fails (e.g. duplicate name, invalid KB)
    """
    organization_id = UUID(user_data.get("org_id"))
    try:
        tool = await tool_service.create_tool(
            organization_id=organization_id,
            name=tool_data.name,
            description=tool_data.description,
            tool_type=tool_data.tool_type,
            knowledge_base_id=tool_data.knowledge_base_id,
            config=tool_data.config,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return _tool_to_response(tool)


@router.put("/{tool_id}", response_model=ToolResponse)
async def update_tool(
    tool_id: UUID,
    tool_data: ToolUpdate,
    user_data: dict = Depends(get_current_user_from_token),
    tool_service: ToolService = Depends(get_tool_service),
):
    """Update a tool.

    Args:
        tool_id: Tool ID
        tool_data: Tool update payload (partial)
        user_data: Current user data from token
        tool_service: Tool service instance

    Returns:
        Updated tool

    Raises:
        HTTPException: If tool not found or validation fails
    """
    organization_id = UUID(user_data.get("org_id"))
    try:
        tool = await tool_service.update_tool(
            tool_id=tool_id,
            organization_id=organization_id,
            name=tool_data.name,
            description=tool_data.description,
            config=tool_data.config,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found",
        )
    return _tool_to_response(tool)


@router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tool(
    tool_id: UUID,
    user_data: dict = Depends(get_current_user_from_token),
    tool_service: ToolService = Depends(get_tool_service),
):
    """Delete a tool. Removes the tool from all agents that use it.

    Args:
        tool_id: Tool ID
        user_data: Current user data from token
        tool_service: Tool service instance

    Raises:
        HTTPException: If tool not found
    """
    organization_id = UUID(user_data.get("org_id"))
    deleted = await tool_service.delete_tool(tool_id=tool_id, organization_id=organization_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found",
        )
