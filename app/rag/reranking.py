from __future__ import annotations

import math
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")

_WORD_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    # simple deterministic tokenizer
    return set(_WORD_RE.findall(text.lower()))


def overlap_score(question: str, chunk_text: str) -> float:
    q = _tokens(question)
    c = _tokens(chunk_text)
    if not q or not c:
        return 0.0

    inter = len(q & c)
    denom = math.sqrt(len(q) * len(c))
    return float(inter) / float(denom) if denom > 0 else 0.0


@dataclass(frozen=True, slots=True)
class RerankedItem(Generic[T]):
    item: T
    score: float


def rerank_by_overlap(
    *,
    question: str,
    items: Iterable[RerankedItem[T]],
    get_text: Callable[[T], str],
    weight: float,
) -> list[RerankedItem[T]]:
    """
    Combine original score with token-overlap score.
    final = (1-weight)*orig + weight*overlap
    """
    w = max(0.0, min(1.0, weight))

    out: list[RerankedItem[T]] = []
    for it in items:
        ov = overlap_score(question, get_text(it.item))
        final = (1.0 - w) * it.score + w * ov
        out.append(RerankedItem(item=it.item, score=final))

    out.sort(key=lambda x: x.score, reverse=True)
    return out
