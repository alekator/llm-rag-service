from __future__ import annotations

from typing import cast

import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.settings import get_settings

_redis: Redis | None = None  # type: ignore


def get_redis() -> Redis:  # type: ignore
    """
    Lazily create a singleton Redis client.
    Safe to call from FastAPI dependencies/handlers.
    """
    global _redis
    if _redis is None:
        s = get_settings()
        _redis = cast(  # type: ignore
            Redis,  # type: ignore
            redis.from_url(
                s.redis_url,
                encoding="utf-8",
                decode_responses=True,
            ),
        )
    return _redis


async def close_redis() -> None:
    """Gracefully close Redis client on shutdown."""
    global _redis
    if _redis is None:
        return
    await _redis.close()
    _redis = None
