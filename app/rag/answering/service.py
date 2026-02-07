from __future__ import annotations

import logging
import time
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.query import SourceChunk
from app.core.settings import get_settings
from app.rag.answering.llm import generate_answer_llm
from app.rag.answering.rerank import rerank_candidates_overlap
from app.rag.answering.types import AnswerTimings
from app.rag.ingestion.embeddings import EmbeddingsClient
from app.repos.chunks import ChunkRepository

logger = logging.getLogger(__name__)


async def answer_question(
    *,
    session: AsyncSession,
    document_id: uuid.UUID,
    question: str,
    top_k: int,
) -> tuple[str | None, list[SourceChunk], AnswerTimings]:
    """
    Core RAG use-case:
    1) Embed question
    2) Vector search (pgvector)
    3) (Optional) Rerank
    4) Build context
    5) (Optional) LLM answer
    """

    s = get_settings()
    chunk_repo = ChunkRepository(session)

    t_total0 = time.perf_counter()

    # candidates_limit: top_k * multiplier
    candidates_limit = top_k
    if s.rerank_backend != "disabled":
        candidates_limit = max(top_k, top_k * int(s.rerank_candidates_multiplier))

    # 1) embed question
    t0 = time.perf_counter()
    try:
        emb = EmbeddingsClient()
        query_vector = (await emb.embed([question]))[0]
    except Exception as e:
        logger.warning("Embedding failed, returning retrieval only: %s", e)
        query_vector = None
    embed_ms = (time.perf_counter() - t0) * 1000.0

    if query_vector is None:
        total_ms = (time.perf_counter() - t_total0) * 1000.0
        return (
            None,
            [],
            AnswerTimings(embed_query_ms=round(embed_ms, 3), total_ms=round(total_ms, 3)),
        )

    # 2) vector search (один раз)
    t0 = time.perf_counter()
    chunks = await chunk_repo.search_with_score(
        document_id=document_id,
        query_embedding=query_vector,
        limit=candidates_limit,
    )
    vector_ms = (time.perf_counter() - t0) * 1000.0

    # 3) rerank (optional)
    rerank_ms = 0.0
    if s.rerank_backend == "overlap" and chunks:
        t0 = time.perf_counter()

        w = float(s.rerank_weight)
        w = 0.0 if w < 0.0 else (1.0 if w > 1.0 else w)

        chunks = rerank_candidates_overlap(
            question=question,
            items=chunks,
            get_text=lambda c: c.text,
            weight=w,
        )[:top_k]

        rerank_ms = (time.perf_counter() - t0) * 1000.0
    else:
        chunks = chunks[:top_k]

    sources: list[SourceChunk] = [
        SourceChunk(chunk_index=c.chunk_index, text=c.text, score=score) for c, score in chunks
    ]

    # 4) context
    context = "\n\n".join(c.text for c, _ in chunks)

    # 5) LLM (optional)
    t0 = time.perf_counter()
    try:
        answer = await generate_answer_llm(question=question, context=context)
    except Exception as e:
        logger.warning("LLM disabled or failed: %s", e)
        answer = None
    llm_ms = (time.perf_counter() - t0) * 1000.0

    total_ms = (time.perf_counter() - t_total0) * 1000.0
    timings = AnswerTimings(
        embed_query_ms=round(embed_ms, 3),
        vector_search_ms=round(vector_ms, 3),
        rerank_ms=round(rerank_ms, 3),
        llm_ms=round(llm_ms, 3),
        total_ms=round(total_ms, 3),
    )

    return answer, sources, timings
