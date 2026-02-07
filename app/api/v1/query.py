import logging
import time
import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.query import QueryMeta, QueryRequest, QueryResponse, QueryTimings
from app.core.settings import get_settings
from app.db.engine import get_session
from app.rag.answering.service import answer_question

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/query", response_model=QueryResponse)  # type: ignore
async def query_endpoint(
    payload: QueryRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> QueryResponse:
    request_id = str(getattr(request.state, "request_id", "")) or str(uuid.uuid4())
    s = get_settings()

    # top_k: default + clamp
    top_k_in = payload.top_k if payload.top_k is not None else int(s.top_k_default)
    top_k = max(1, min(int(top_k_in), int(s.top_k_max)))

    # candidates_limit: top_k * multiplier
    candidates_limit = top_k
    if getattr(s, "rerank_backend", "stub") != "disabled":
        candidates_limit = max(top_k, top_k * int(getattr(s, "rerank_candidates_multiplier", 3)))

    t0 = time.perf_counter()

    answer, sources = await answer_question(
        session=session,
        document_id=payload.document_id,
        question=payload.question,
        top_k=top_k,
    )
    t_total = (time.perf_counter() - t0) * 1000.0

    timings = QueryTimings(
        embed_query_ms=0.0,
        vector_search_ms=0.0,
        rerank_ms=0.0,
        llm_ms=0.0,
        total_ms=round(t_total, 3),
    )

    meta = QueryMeta(
        top_k=top_k,
        candidates_limit=candidates_limit,
        rerank_backend=str(getattr(s, "rerank_backend", "stub")),
        reranker=str(getattr(s, "reranker", "none")),
        rerank_weight=float(getattr(s, "rerank_weight", 0.0)),
        rerank_alpha=float(getattr(s, "rerank_alpha", 0.7)),
    )

    logger.info(
        "query request_id=%s doc=%s top_k=%s total_ms=%.2f",
        request_id,
        payload.document_id,
        top_k,
        timings.total_ms,
    )

    return QueryResponse(
        request_id=request_id,
        answer=answer,
        sources=sources,
        meta=meta,
        timings=timings,
    )
