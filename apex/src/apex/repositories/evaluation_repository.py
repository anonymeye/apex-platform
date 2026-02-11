"""Evaluation run and score repositories."""

from datetime import datetime, timezone
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

    async def get_by_id_and_organization(
        self,
        id: UUID,
        organization_id: UUID,
    ) -> Optional[EvaluationJudgeConfig]:
        """Get a judge config by ID and organization."""
        result = await self.session.execute(
            select(EvaluationJudgeConfig).where(
                EvaluationJudgeConfig.id == id,
                EvaluationJudgeConfig.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

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

    def _list_query(
        self,
        organization_id: UUID,
        status: Optional[str] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
    ):
        """Base query for list/count with filters."""
        q = select(EvaluationRun).where(
            EvaluationRun.organization_id == organization_id
        )
        if status is not None:
            q = q.where(EvaluationRun.status == status)
        if created_after is not None:
            q = q.where(EvaluationRun.created_at >= created_after)
        if created_before is not None:
            q = q.where(EvaluationRun.created_at <= created_before)
        return q

    async def count_by_organization(
        self,
        organization_id: UUID,
        status: Optional[str] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
    ) -> int:
        """Count runs for an organization with optional filters."""
        from sqlalchemy import func

        q = select(func.count()).select_from(EvaluationRun).where(
            EvaluationRun.organization_id == organization_id
        )
        if status is not None:
            q = q.where(EvaluationRun.status == status)
        if created_after is not None:
            q = q.where(EvaluationRun.created_at >= created_after)
        if created_before is not None:
            q = q.where(EvaluationRun.created_at <= created_before)
        result = await self.session.execute(q)
        return result.scalar() or 0

    async def list_by_organization(
        self,
        organization_id: UUID,
        status: Optional[str] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[EvaluationRun]:
        """List runs for an organization, optionally filtered by status and time."""
        q = (
            self._list_query(
                organization_id,
                status=status,
                created_after=created_after,
                created_before=created_before,
            )
            .order_by(EvaluationRun.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
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

    async def get_by_id_and_run_id(
        self, score_id: UUID, run_id: UUID
    ) -> Optional[EvaluationScore]:
        """Get a score by ID and run_id (ensures score belongs to the run)."""
        result = await self.session.execute(
            select(EvaluationScore).where(
                EvaluationScore.id == score_id,
                EvaluationScore.run_id == run_id,
            )
        )
        return result.scalar_one_or_none()

    async def set_human_review(
        self,
        score_id: UUID,
        run_id: UUID,
        human_score: float,
        human_comment: Optional[str] = None,
    ) -> Optional[EvaluationScore]:
        """Set human score and comment on a score; returns updated score or None if not found."""
        score = await self.get_by_id_and_run_id(score_id, run_id)
        if not score:
            return None
        score.human_score = human_score
        score.human_comment = human_comment
        score.human_reviewed_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(score)
        return score
