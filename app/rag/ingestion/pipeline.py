from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_session
from app.rag.ingestion.chunking import chunk_text
from app.rag.ingestion.embeddings import EmbeddingsClient
from app.repos.chunks import ChunkRepository
from app.repos.documents import DocumentRepository


async def ingest_text_document_bg(*, document_id: uuid.UUID, text: str) -> None:
    async for session in get_session():
        try:
            await ingest_text_document(session=session, document_id=document_id, text=text)
        except Exception as e:
            doc_repo = DocumentRepository(session)
            await doc_repo.set_status(document_id=document_id, status="failed", error=str(e))
            await session.commit()
        break


async def ingest_text_document(
    *,
    session: AsyncSession,
    document_id: uuid.UUID,
    text: str,
) -> None:
    doc_repo = DocumentRepository(session)
    chunk_repo = ChunkRepository(session)
    emb = EmbeddingsClient()

    await doc_repo.set_status(document_id=document_id, status="processing")
    await session.commit()

    try:
        chunks = chunk_text(text)
        if not chunks:
            await doc_repo.set_status(
                document_id=document_id, status="failed", error="Empty document text"
            )
            await session.commit()
            return

        vectors = await emb.embed(chunks)

        for idx, (ch, vec) in enumerate(zip(chunks, vectors, strict=True)):
            await chunk_repo.add_chunk(
                document_id=document_id,
                chunk_index=idx,
                text=ch,
                embedding=vec,
                page=None,
            )

        await doc_repo.set_status(document_id=document_id, status="ready")
        await session.commit()

    except Exception as e:
        await doc_repo.set_status(document_id=document_id, status="failed", error=str(e))
        await session.commit()
        raise
