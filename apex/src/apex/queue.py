"""Redis-backed job queue for evaluation runs."""

from __future__ import annotations

import logging
from uuid import UUID

from redis.asyncio import Redis

logger = logging.getLogger(__name__)

# Redis list key for evaluation run jobs (payload: run_id as string)
EVAL_QUEUE_KEY = "apex:evaluation:queue"


async def enqueue_evaluation_run(redis: Redis, run_id: UUID) -> None:
    """Push an evaluation run onto the queue. Worker will process it via BLPOP."""
    if redis is None:
        raise ValueError("Redis client is required to enqueue evaluation jobs")
    key = EVAL_QUEUE_KEY
    await redis.rpush(key, str(run_id))
    logger.info("Enqueued evaluation run %s", run_id)


async def dequeue_evaluation_job(
    redis: Redis,
    timeout_seconds: int = 30,
) -> UUID | None:
    """
    Block until a job is available or timeout. Returns run_id or None on timeout.
    Uses BLPOP so only one worker consumes each job.
    """
    if redis is None:
        return None
    result = await redis.blpop(EVAL_QUEUE_KEY, timeout=timeout_seconds)
    if result is None:
        return None
    # result is (key, value) e.g. (b'apex:evaluation:queue', b'...uuid...')
    _, value = result
    raw = value.decode("utf-8") if isinstance(value, bytes) else value
    try:
        return UUID(raw)
    except (ValueError, TypeError):
        logger.warning("Invalid run_id in queue: %s", raw)
        return None
