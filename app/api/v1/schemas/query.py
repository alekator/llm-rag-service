from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class QueryMeta(BaseModel):
    top_k: int
    candidates_limit: int
    rerank_backend: str
    reranker: str
    rerank_weight: float
    rerank_alpha: float


class QueryTimings(BaseModel):
    embed_query_ms: float = Field(ge=0)
    vector_search_ms: float = Field(ge=0)
    rerank_ms: float = Field(ge=0)
    llm_ms: float = Field(ge=0)
    total_ms: float = Field(ge=0)


class QueryRequest(BaseModel):
    document_id: uuid.UUID
    question: str
    top_k: int = 5


class SourceChunk(BaseModel):
    chunk_index: int
    text: str
    score: float


class QueryResponse(BaseModel):
    request_id: str
    answer: str | None
    sources: list[SourceChunk] = Field(default_factory=list)
    meta: QueryMeta
    timings: QueryTimings
