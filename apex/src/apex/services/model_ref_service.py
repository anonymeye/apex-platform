"""Model reference management service."""

import logging
from typing import Optional
from uuid import UUID

from apex.models.model_ref import ModelRef
from apex.repositories.connection_repository import ConnectionRepository
from apex.repositories.model_ref_repository import ModelRefRepository

logger = logging.getLogger(__name__)


class ModelRefService:
    def __init__(self, repo: ModelRefRepository, connection_repo: ConnectionRepository):
        self.repo = repo
        self.connection_repo = connection_repo

    async def create_model_ref(
        self,
        *,
        organization_id: UUID,
        name: str,
        runtime_id: str,
        connection_id: UUID,
        config: Optional[dict] = None,
    ) -> ModelRef:
        conn = await self.connection_repo.get_for_org(connection_id, organization_id)
        if not conn:
            raise ValueError(f"Connection {connection_id} not found")

        model_ref = await self.repo.create(
            organization_id=organization_id,
            name=name,
            runtime_id=runtime_id,
            connection_id=connection_id,
            config=config or {},
        )
        logger.info(f"Created model ref {model_ref.id} ({model_ref.name})")
        return await self.repo.get_for_org(model_ref.id, organization_id) or model_ref

    async def get_model_ref(self, model_ref_id: UUID, organization_id: UUID) -> Optional[ModelRef]:
        return await self.repo.get_for_org(model_ref_id, organization_id)

    async def list_model_refs(self, organization_id: UUID, skip: int = 0, limit: int = 100) -> list[ModelRef]:
        return await self.repo.get_by_organization(organization_id, skip=skip, limit=limit)

    async def update_model_ref(
        self, model_ref_id: UUID, organization_id: UUID, **kwargs
    ) -> Optional[ModelRef]:
        existing = await self.repo.get_for_org(model_ref_id, organization_id)
        if not existing:
            return None

        if "connection_id" in kwargs and kwargs["connection_id"] is not None:
            conn = await self.connection_repo.get_for_org(kwargs["connection_id"], organization_id)
            if not conn:
                raise ValueError(f"Connection {kwargs['connection_id']} not found")

        if "config" in kwargs and kwargs["config"] is not None:
            kwargs["config"] = {**(existing.config or {}), **kwargs["config"]}

        updated = await self.repo.update(model_ref_id, **{k: v for k, v in kwargs.items() if v is not None})
        if not updated:
            return None
        return await self.repo.get_for_org(model_ref_id, organization_id)

    async def delete_model_ref(self, model_ref_id: UUID, organization_id: UUID) -> bool:
        existing = await self.repo.get_for_org(model_ref_id, organization_id)
        if not existing:
            return False
        return await self.repo.delete(model_ref_id)

