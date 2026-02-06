from __future__ import annotations

import uuid

from pydantic import BaseModel


class QueryRequest(BaseModel):
    document_id: uuid.UUID
    question: str
    top_k: int = 5


class SourceChunk(BaseModel):
    chunk_index: int
    text: str
    score: float


class QueryResponse(BaseModel):
    answer: str | None
    sources: list[SourceChunk]
