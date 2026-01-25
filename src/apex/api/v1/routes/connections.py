"""Connection endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apex.api.dependencies import get_current_user_from_token
from apex.api.v1.schemas.connections import (
    ConnectionCreate,
    ConnectionResponse,
    ConnectionUpdate,
)
from apex.core.database import get_db
from apex.repositories.connection_repository import ConnectionRepository
from apex.services.connection_service import ConnectionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/connections", tags=["connections"])


def get_connection_service(db: AsyncSession = Depends(get_db)) -> ConnectionService:
    return ConnectionService(ConnectionRepository(db))


def _to_response(conn) -> ConnectionResponse:
    return ConnectionResponse(
        id=conn.id,
        name=conn.name,
        connection_type=conn.connection_type,
        provider=conn.provider,
        base_url=conn.base_url,
        auth_type=conn.auth_type,
        api_key_env_var=conn.api_key_env_var,
        config=conn.config,
        organization_id=conn.organization_id,
        created_at=conn.created_at.isoformat(),
        updated_at=conn.updated_at.isoformat(),
    )


@router.post("", response_model=ConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_connection(
    payload: ConnectionCreate,
    user_data: dict = Depends(get_current_user_from_token),
    svc: ConnectionService = Depends(get_connection_service),
):
    organization_id = UUID(user_data.get("org_id"))
    conn = await svc.create_connection(
        organization_id=organization_id,
        name=payload.name,
        connection_type=payload.connection_type,
        provider=payload.provider,
        base_url=payload.base_url,
        auth_type=payload.auth_type,
        api_key_env_var=payload.api_key_env_var,
        config=payload.config,
    )
    return _to_response(conn)


@router.get("", response_model=list[ConnectionResponse])
async def list_connections(
    skip: int = 0,
    limit: int = 100,
    user_data: dict = Depends(get_current_user_from_token),
    svc: ConnectionService = Depends(get_connection_service),
):
    organization_id = UUID(user_data.get("org_id"))
    conns = await svc.list_connections(organization_id, skip=skip, limit=limit)
    return [_to_response(c) for c in conns]


@router.get("/{connection_id}", response_model=ConnectionResponse)
async def get_connection(
    connection_id: UUID,
    user_data: dict = Depends(get_current_user_from_token),
    svc: ConnectionService = Depends(get_connection_service),
):
    organization_id = UUID(user_data.get("org_id"))
    conn = await svc.get_connection(connection_id, organization_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    return _to_response(conn)


@router.put("/{connection_id}", response_model=ConnectionResponse)
async def update_connection(
    connection_id: UUID,
    payload: ConnectionUpdate,
    user_data: dict = Depends(get_current_user_from_token),
    svc: ConnectionService = Depends(get_connection_service),
):
    organization_id = UUID(user_data.get("org_id"))
    try:
        conn = await svc.update_connection(
            connection_id,
            organization_id,
            name=payload.name,
            connection_type=payload.connection_type,
            provider=payload.provider,
            base_url=payload.base_url,
            auth_type=payload.auth_type,
            api_key_env_var=payload.api_key_env_var,
            config=payload.config,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    return _to_response(conn)


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    connection_id: UUID,
    user_data: dict = Depends(get_current_user_from_token),
    svc: ConnectionService = Depends(get_connection_service),
):
    organization_id = UUID(user_data.get("org_id"))
    ok = await svc.delete_connection(connection_id, organization_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Connection not found")
    return None

