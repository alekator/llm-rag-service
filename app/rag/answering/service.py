import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.query import SourceChunk
from app.core.settings import get_settings
from app.rag.answering.llm import generate_answer_llm
from app.rag.answering.rerank import rerank_candidates_overlap
from app.rag.ingestion.embeddings import EmbeddingsClient
from app.repos.chunks import ChunkRepository

logger = logging.getLogger(__name__)


async def answer_question(
    *,
    session: AsyncSession,
    document_id: uuid.UUID,
    question: str,
    top_k: int,
) -> tuple[str | None, list[SourceChunk]]:
    """
    Core RAG use-case:
    1. Embed question
    2. Vector search
    3. Build context
    4. (Optional) LLM answer
    """

    chunk_repo = ChunkRepository(session)

    # 1. embed question
    try:
        emb = EmbeddingsClient()
        query_vector = (await emb.embed([question]))[0]
    except Exception as e:
        logger.warning("Embedding failed, returning retrieval only: %s", e)
        query_vector = None

    # 2. vector search
    if query_vector is None:
        return None, []

    chunks = await chunk_repo.search_with_score(
        document_id=document_id,
        query_embedding=query_vector,
        limit=top_k,
    )

    s = get_settings()

    candidates_limit = top_k
    if s.rerank_backend != "disabled":
        candidates_limit = max(top_k, top_k * int(s.rerank_candidates_multiplier))

    chunks = await chunk_repo.search_with_score(
        document_id=document_id,
        query_embedding=query_vector,
        limit=candidates_limit,
    )

    if s.rerank_backend == "overlap" and chunks:
        w = float(s.rerank_weight)
        w = 0.0 if w < 0.0 else (1.0 if w > 1.0 else w)

        chunks = rerank_candidates_overlap(
            question=question,
            items=chunks,
            get_text=lambda c: c.text,
            weight=w,
        )[:top_k]
    else:
        chunks = chunks[:top_k]

    sources: list[SourceChunk] = [
        SourceChunk(
            chunk_index=c.chunk_index,
            text=c.text,
            score=score,
        )
        for c, score in chunks
    ]

    # 3. context
    context = "\n\n".join(c.text for c, _ in chunks)

    # 4. LLM (optional)
    try:
        answer = await generate_answer_llm(question=question, context=context)
    except Exception as e:
        logger.warning("LLM disabled or failed: %s", e)
        answer = None

    return answer, sources
