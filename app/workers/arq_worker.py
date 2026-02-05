from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, ClassVar

from arq.connections import RedisSettings

from app.core.settings import get_settings
from app.db.engine import close_engine, get_session, init_engine
from app.rag.ingestion.pipeline import ingest_text_document
from app.repos.documents import DocumentRepository


async def startup(ctx: Any) -> None:
    init_engine()


async def shutdown(ctx: Any) -> None:
    await close_engine()


async def ingest_document(ctx: Any, *, document_id: str, file_path: str) -> None:
    doc_id = uuid.UUID(document_id)

    # читаем файл (пока только как текст)
    path = Path(file_path)
    with path.open("rb") as f:
        data = f.read()
    text = data.decode("utf-8", errors="replace")

    async for session in get_session():
        repo = DocumentRepository(session)
        try:
            await ingest_text_document(session=session, document_id=doc_id, text=text)
        except Exception as e:
            await repo.set_status(document_id=doc_id, status="failed", error=str(e))
            await session.commit()
            raise
        break


class WorkerSettings:
    settings = get_settings()
    functions: ClassVar[list[Callable[..., Awaitable[Any]]]] = [ingest_document]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)

    # "production-like" границы
    job_timeout = 600  # 10 минут
    max_tries = 3
