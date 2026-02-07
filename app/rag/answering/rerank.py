from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from app.rag.reranking import RerankedItem, rerank_by_overlap

T = TypeVar("T")


def rerank_candidates_overlap(
    *,
    question: str,
    items: list[tuple[T, float]],
    get_text: Callable[[T], str],
    weight: float,
) -> list[tuple[T, float]]:
    """
    items: list of (item, original_score) where higher score is better.
    returns: same shape, but sorted by blended score (vector+overlap).
    """
    reranked_items = [RerankedItem(item=obj, score=float(score)) for (obj, score) in items]

    reranked = rerank_by_overlap(
        question=question,
        items=reranked_items,
        get_text=get_text,
        weight=weight,
    )

    return [(ri.item, ri.score) for ri in reranked]
