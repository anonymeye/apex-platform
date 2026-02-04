"""Seed data script.

This is a lightweight helper for local/dev environments.

It creates (if missing):
- a default Connection
- a default ModelRef under that connection

Usage (example):
  ORG_ID=<uuid> python -m apex.scripts.seed_data
"""

import asyncio
import os
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from apex.core.config import settings
from apex.models.connection import Connection
from apex.models.model_ref import ModelRef
from apex.models.user import Organization


async def _pick_org_id(session: AsyncSession) -> UUID:
    org_id_env = os.getenv("ORG_ID")
    if org_id_env:
        return UUID(org_id_env)

    result = await session.execute(select(Organization.id).limit(1))
    org_id = result.scalar_one_or_none()
    if not org_id:
        raise RuntimeError("No organizations found. Set ORG_ID or create an organization first.")
    return org_id


async def seed_defaults() -> None:
    engine = create_async_engine(settings.database_url, echo=settings.debug, future=True)
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as session:
        org_id = await _pick_org_id(session)

        # Connection defaults
        default_connection_name = os.getenv("DEFAULT_CONNECTION_NAME", "Default OpenAI")
        default_connection_type = os.getenv("DEFAULT_CONNECTION_TYPE", "vendor_api")
        default_provider = os.getenv("DEFAULT_PROVIDER", "openai")
        default_auth_type = os.getenv("DEFAULT_AUTH_TYPE", "env")
        default_api_key_env_var = os.getenv("DEFAULT_API_KEY_ENV_VAR", "OPENAI_API_KEY")
        default_base_url = os.getenv("DEFAULT_BASE_URL")  # optional

        # Model defaults
        default_model_name = os.getenv("DEFAULT_MODEL_NAME", "GPT-4o Mini")
        default_runtime_id = os.getenv("DEFAULT_MODEL_RUNTIME_ID", "gpt-4o-mini")

        # Create connection if none exist
        conn_result = await session.execute(
            select(Connection).where(Connection.organization_id == org_id).limit(1)
        )
        conn = conn_result.scalar_one_or_none()
        if not conn:
            conn = Connection(
                organization_id=org_id,
                name=default_connection_name,
                connection_type=default_connection_type,
                provider=default_provider,
                base_url=default_base_url,
                auth_type=default_auth_type,
                api_key_env_var=default_api_key_env_var,
                config={},
            )
            session.add(conn)
            await session.flush()

        # Create model ref if none exist
        mr_result = await session.execute(
            select(ModelRef).where(ModelRef.organization_id == org_id).limit(1)
        )
        mr = mr_result.scalar_one_or_none()
        if not mr:
            mr = ModelRef(
                organization_id=org_id,
                connection_id=conn.id,
                name=default_model_name,
                runtime_id=default_runtime_id,
                config={},
            )
            session.add(mr)
            await session.flush()

        await session.commit()

    await engine.dispose()


def main() -> None:
    asyncio.run(seed_defaults())


if __name__ == "__main__":
    main()
