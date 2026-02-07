from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI

from app.api.v1.router import router as v1_router
from app.core.middleware import RequestIdLoggingMiddleware
from app.core.settings import get_settings
from app.db.engine import close_engine, init_engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    init_engine()

    app.state.redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    try:
        yield
    finally:
        await app.state.redis.close()
        await close_engine()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
    )
    app.add_middleware(RequestIdLoggingMiddleware)

    app.include_router(v1_router, prefix=settings.api_v1_prefix)
    app.add_middleware(RequestIdLoggingMiddleware)
    return app


app = create_app()
