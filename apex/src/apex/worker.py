"""
Evaluation worker: consumes jobs from Redis queue, runs judge, persists scores.

Run with: python -m apex.worker

Uses same env as API: DATABASE_URL, REDIS_URL, judge API keys (e.g. OPENAI_API_KEY).
"""

from __future__ import annotations

import asyncio
import logging
import signal
import sys

from dotenv import load_dotenv

load_dotenv(override=True)

from redis.asyncio import Redis

from apex.core.config import settings
from apex.core.database import AsyncSessionLocal, close_db
from apex.queue import dequeue_evaluation_job
from apex.repositories.evaluation_repository import (
    EvaluationRunRepository,
    EvaluationScoreRepository,
)
from apex.services.evaluation_service import EvaluationService
from apex.storage.conversation_state_store import ConversationStateStore
from apex.utils.logging import setup_logging

logger = logging.getLogger(__name__)

_shutdown = False


def _handle_signal(_signum, _frame):
    global _shutdown
    _shutdown = True
    logger.info("Shutdown requested, finishing current job then exiting")


async def run_worker_loop(redis: Redis) -> None:
    """Process evaluation jobs until shutdown."""
    global _shutdown
    while not _shutdown:
        run_id = await dequeue_evaluation_job(redis, timeout_seconds=30)
        if run_id is None:
            continue
        logger.info("Processing evaluation run %s", run_id)
        async with AsyncSessionLocal() as session:
            try:
                run_repo = EvaluationRunRepository(session)
                score_repo = EvaluationScoreRepository(session)
                store = ConversationStateStore(
                    redis,
                    ttl_seconds=settings.conversation_state_ttl_seconds,
                )
                svc = EvaluationService(
                    run_repo=run_repo,
                    score_repo=score_repo,
                    conversation_state_store=store,
                )
                await svc.execute_run(run_id)
                await session.commit()
                logger.info("Completed evaluation run %s", run_id)
            except Exception as e:
                await session.rollback()
                logger.exception("Evaluation run %s failed: %s", run_id, e)
                try:
                    run_repo = EvaluationRunRepository(session)
                    await run_repo.update(
                        run_id,
                        status="failed",
                        error_message=str(e),
                    )
                    await session.commit()
                except Exception:
                    await session.rollback()


async def main() -> None:
    """Connect to Redis and run the worker loop."""
    setup_logging(debug=settings.debug, log_level=settings.log_level)
    logger.info("Evaluation worker starting (redis_url=%s)", settings.redis_url.split("@")[-1] if "@" in settings.redis_url else "local")

    try:
        redis = Redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    except Exception as e:
        logger.error("Failed to connect to Redis: %s", e, exc_info=True)
        sys.exit(1)

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    try:
        await run_worker_loop(redis)
    finally:
        await redis.aclose()
        await close_db()
        logger.info("Evaluation worker stopped")


if __name__ == "__main__":
    asyncio.run(main())
