from __future__ import annotations

import uuid
from typing import cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Document


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, filename: str, content_type: str) -> Document:
        doc = Document(filename=filename, content_type=content_type, status="uploaded")
        self._session.add(doc)
        await self._session.flush()
        return doc

    async def get(self, *, document_id: uuid.UUID) -> Document | None:
        res = await self._session.execute(select(Document).where(Document.id == document_id))
        doc = cast(Document | None, res.scalar_one_or_none())
        return doc

    async def set_status(
        self, *, document_id: uuid.UUID, status: str, error: str | None = None
    ) -> None:
        doc = await self.get(document_id=document_id)
        if doc is None:
            return
        doc.status = status
        doc.error = error
