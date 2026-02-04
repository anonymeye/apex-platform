"""Evaluation run and score repositories."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apex.models.evaluation import (
    EvaluationJudgeConfig,
    EvaluationRun,
    EvaluationScore,
)
from apex.repositories.base import BaseRepository


class EvaluationJudgeConfigRepository(BaseRepository[EvaluationJudgeConfig]):
    """Repository for evaluation judge configs."""

    def __init__(self, session: AsyncSession):
        super().__init__(EvaluationJudgeConfig, session)

    async def get_by_organization(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[EvaluationJudgeConfig]:
        """List judge configs for an organization."""
        result = await self.session.execute(
            select(EvaluationJudgeConfig)
            .where(EvaluationJudgeConfig.organization_id == organization_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())


class EvaluationRunRepository(BaseRepository[EvaluationRun]):
    """Repository for evaluation runs."""

    def __init__(self, session: AsyncSession):
        super().__init__(EvaluationRun, session)

    async def get_with_scores(self, id: UUID) -> Optional[EvaluationRun]:
        """Get run with scores loaded."""
        result = await self.session.execute(
            select(EvaluationRun)
            .where(EvaluationRun.id == id)
            .options(selectinload(EvaluationRun.scores))
        )
        return result.scalar_one_or_none()

    async def list_by_organization(
        self,
        organization_id: UUID,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[EvaluationRun]:
        """List runs for an organization, optionally filtered by status."""
        q = select(EvaluationRun).where(
            EvaluationRun.organization_id == organization_id
        )
        if status is not None:
            q = q.where(EvaluationRun.status == status)
        q = q.order_by(EvaluationRun.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(q)
        return list(result.scalars().all())


class EvaluationScoreRepository(BaseRepository[EvaluationScore]):
    """Repository for evaluation scores."""

    def __init__(self, session: AsyncSession):
        super().__init__(EvaluationScore, session)

    async def list_by_run_id(
        self,
        run_id: UUID,
        skip: int = 0,
        limit: int = 500,
    ) -> list[EvaluationScore]:
        """List scores for a run (paginated)."""
        result = await self.session.execute(
            select(EvaluationScore)
            .where(EvaluationScore.run_id == run_id)
            .order_by(EvaluationScore.created_at)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_run_id(self, run_id: UUID) -> int:
        """Return the number of scores for a run."""
        from sqlalchemy import func

        result = await self.session.execute(
            select(func.count()).select_from(EvaluationScore).where(
                EvaluationScore.run_id == run_id
            )
        )
        return result.scalar() or 0
