"""Connection management service."""

import logging
from typing import Optional
from uuid import UUID

from apex.models.connection import Connection
from apex.repositories.connection_repository import ConnectionRepository

logger = logging.getLogger(__name__)


class ConnectionService:
    def __init__(self, repo: ConnectionRepository):
        self.repo = repo

    async def create_connection(
        self,
        *,
        organization_id: UUID,
        name: str,
        connection_type: str,
        provider: str,
        base_url: Optional[str] = None,
        auth_type: str,
        api_key_env_var: Optional[str] = None,
        config: Optional[dict] = None,
    ) -> Connection:
        conn = await self.repo.create(
            organization_id=organization_id,
            name=name,
            connection_type=connection_type,
            provider=provider,
            base_url=base_url,
            auth_type=auth_type,
            api_key_env_var=api_key_env_var,
            config=config or {},
        )
        logger.info(f"Created connection {conn.id} ({conn.name})")
        return conn

    async def get_connection(self, connection_id: UUID, organization_id: UUID) -> Optional[Connection]:
        return await self.repo.get_for_org(connection_id, organization_id)

    async def list_connections(self, organization_id: UUID, skip: int = 0, limit: int = 100) -> list[Connection]:
        return await self.repo.get_by_organization(organization_id, skip=skip, limit=limit)

    async def update_connection(
        self, connection_id: UUID, organization_id: UUID, **kwargs
    ) -> Optional[Connection]:
        existing = await self.repo.get_for_org(connection_id, organization_id)
        if not existing:
            return None

        # Merge config if provided
        if "config" in kwargs and kwargs["config"] is not None:
            kwargs["config"] = {**(existing.config or {}), **kwargs["config"]}

        updated = await self.repo.update(connection_id, **{k: v for k, v in kwargs.items() if v is not None})
        if updated:
            logger.info(f"Updated connection {connection_id}")
        return updated

    async def delete_connection(self, connection_id: UUID, organization_id: UUID) -> bool:
        existing = await self.repo.get_for_org(connection_id, organization_id)
        if not existing:
            return False
        return await self.repo.delete(connection_id)

