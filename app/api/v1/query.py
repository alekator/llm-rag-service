from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.query import QueryRequest, QueryResponse
from app.db.engine import get_session
from app.rag.answering.service import answer_question

router = APIRouter()


@router.post("/query", response_model=QueryResponse)  # type: ignore[misc]
async def query_document(
    payload: QueryRequest,
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> QueryResponse:
    answer, sources = await answer_question(
        session=session,
        document_id=payload.document_id,
        question=payload.question,
        top_k=payload.top_k,
    )

    return QueryResponse(answer=answer, sources=sources)
