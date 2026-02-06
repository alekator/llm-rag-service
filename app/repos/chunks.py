from __future__ import annotations

import uuid
from typing import cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Chunk


class ChunkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_chunk(
        self,
        *,
        document_id: uuid.UUID,
        chunk_index: int,
        text: str,
        embedding: list[float] | None,
        page: int | None = None,
    ) -> Chunk:
        chunk = Chunk(
            document_id=document_id,
            chunk_index=chunk_index,
            page=page,
            text=text,
            embedding=embedding,
        )
        self._session.add(chunk)
        return chunk

    async def search_by_embedding(
        self,
        *,
        document_id: uuid.UUID,
        query_embedding: list[float],
        limit: int = 5,
    ) -> list[Chunk]:
        # cosine distance: smaller is closer
        stmt = (
            select(Chunk)
            .where(Chunk.document_id == document_id)
            .where(Chunk.embedding.is_not(None))
            .order_by(Chunk.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )
        res = await self._session.execute(stmt)
        rows = res.scalars().all()
        return cast(list[Chunk], rows)

    async def search_with_score(
        self,
        *,
        document_id: uuid.UUID,
        query_embedding: list[float],
        limit: int,
    ) -> list[tuple[Chunk, float]]:
        """
        Returns (Chunk, score) where lower distance => higher score
        """
        distance = Chunk.embedding.cosine_distance(query_embedding)

        stmt = (
            select(Chunk, distance.label("distance"))
            .where(Chunk.document_id == document_id)
            .where(Chunk.embedding.is_not(None))
            .order_by(distance)
            .limit(limit)
        )

        res = await self._session.execute(stmt)

        rows: list[tuple[Chunk, float]] = []
        for chunk, dist in res.all():
            score = 1.0 / (1.0 + dist) if dist is not None else 0.0
            rows.append((chunk, score))

        return rows
