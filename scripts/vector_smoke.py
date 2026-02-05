from __future__ import annotations

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import close_engine, get_session, init_engine
from app.db.models import Document
from app.repos.chunks import ChunkRepository


async def main() -> None:
    init_engine()

    async for session in get_session():
        session = session
        assert isinstance(session, AsyncSession)

        # 1) создаём документ
        doc = Document(filename="smoke.txt", content_type="text/plain", status="ready")
        session.add(doc)
        await session.flush()  # получим doc.id

        # 2) вставим пару чанков фейковыми embedding (длины 1536)
        e1 = [0.0] * 1536
        e2 = [0.0] * 1536
        e2[0] = 1.0

        repo = ChunkRepository(session)
        await repo.add_chunk(
            document_id=doc.id, chunk_index=0, text="hello world", embedding=e1, page=1
        )
        await repo.add_chunk(
            document_id=doc.id, chunk_index=1, text="vector search works", embedding=e2, page=1
        )

        await session.commit()

        # 3) поиск: запрос ближе к e2
        q = [0.0] * 1536
        q[0] = 1.0

        hits = await repo.search_by_embedding(document_id=doc.id, query_embedding=q, limit=2)

        print("DOC:", doc.id)
        print("HITS:")
        for h in hits:
            print("-", h.chunk_index, h.text)

        break  # важно: нам нужна одна сессия и один прогон

    await close_engine()


if __name__ == "__main__":
    asyncio.run(main())
