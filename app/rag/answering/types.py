from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AnswerTimings:
    embed_query_ms: float = 0.0
    vector_search_ms: float = 0.0
    rerank_ms: float = 0.0
    llm_ms: float = 0.0
    total_ms: float = 0.0
