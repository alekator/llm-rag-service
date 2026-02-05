from __future__ import annotations

import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_session
from app.infra.storage import LocalStorage
from app.rag.ingestion.pipeline import ingest_text_document_bg
from app.repos.documents import DocumentRepository

logger = logging.getLogger(__name__)
router = APIRouter()
storage = LocalStorage()


@router.post("/documents")  # type: ignore[misc]
async def upload_document(
    background: BackgroundTasks,
    file: Annotated[UploadFile, File(...)],
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> dict[str, str]:
    filename = file.filename or "upload.bin"
    content_type = file.content_type or "application/octet-stream"

    # fallback для curl/windows (часто шлёт octet-stream)
    if content_type == "application/octet-stream":
        lower = filename.lower()
        if lower.endswith((".txt", ".md", ".log", ".csv", ".json")):
            content_type = "text/plain"

    repo = DocumentRepository(session)
    doc = await repo.create(filename=filename, content_type=content_type)
    await session.commit()

    data = await file.read()
    storage.save_bytes(document_id=doc.id, filename=filename, data=data)

    if content_type.startswith("text/"):
        text = data.decode("utf-8", errors="replace")
        background.add_task(ingest_text_document_bg, document_id=doc.id, text=text)

    else:
        await repo.set_status(
            document_id=doc.id, status="failed", error="Only text/* supported in v1"
        )
        await session.commit()

    return {"document_id": str(doc.id), "status": doc.status}


@router.get("/documents/{document_id}")  # type: ignore[misc]
async def get_document_status(
    document_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> dict[str, str | None]:
    repo = DocumentRepository(session)
    doc = await repo.get(document_id=document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"document_id": str(doc.id), "status": doc.status, "error": doc.error}
