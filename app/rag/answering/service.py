import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.query import SourceChunk
from app.core.settings import get_settings
from app.rag.answering.llm import generate_answer_llm
from app.rag.answering.rerank import rerank_stub
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

    # 2.5 rerank (deterministic stub)
    s = get_settings()
    if getattr(s, "rerank_backend", "stub") == "stub" and chunks:
        texts = [c.text for c, _ in chunks]
        vector_scores = [score for _, score in chunks]
        order = rerank_stub(
            question=question,
            texts=texts,
            vector_scores=vector_scores,
            alpha=float(getattr(s, "rerank_alpha", 0.7)),
        )
        chunks = [chunks[i] for i in order]

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
