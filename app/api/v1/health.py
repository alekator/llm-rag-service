from __future__ import annotations

from typing import no_type_check

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_session
from app.infra.redis import get_redis

router = APIRouter()


@router.get("/health")
@no_type_check
async def health(session: AsyncSession = Depends(get_session)) -> dict[str, str]:  # noqa: B008
    await session.execute(text("SELECT 1"))
    return {"status": "ok", "db": "ok"}


@router.get("/ready")  # type: ignore
async def ready(session: AsyncSession = Depends(get_session)) -> dict[str, str]:  # noqa: B008
    # Postgres check
    await session.execute(text("SELECT 1"))

    # Redis check
    r: Redis = get_redis()  # type: ignore
    await r.ping()

    return {"status": "ready"}
