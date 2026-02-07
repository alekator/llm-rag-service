from __future__ import annotations

import re
from dataclasses import dataclass

_WORD_RE = re.compile(r"[a-zA-Z0-9_]+")


def _tokenize(text: str) -> list[str]:
    return _WORD_RE.findall(text.lower())


def _lexical_score(question: str, chunk_text: str) -> float:
    """
    Deterministic lexical relevance:
    - token overlap (precision-like)
    - small bonus for exact substring match
    """
    q_tokens = _tokenize(question)
    if not q_tokens:
        return 0.0

    c_tokens = _tokenize(chunk_text)
    if not c_tokens:
        return 0.0

    q_set = set(q_tokens)
    c_set = set(c_tokens)

    overlap = len(q_set & c_set)
    # normalize to [0..1] (ish)
    score = overlap / max(1, len(q_set))

    # bonus if whole question (or big part) appears
    q_norm = " ".join(q_tokens)
    c_norm = " ".join(c_tokens)
    if q_norm and q_norm in c_norm:
        score += 0.2

    return min(score, 1.0)


@dataclass(frozen=True)
class RerankedItem:
    index: int
    combined_score: float


def rerank_stub(
    *,
    question: str,
    texts: list[str],
    vector_scores: list[float],
    alpha: float = 0.7,
) -> list[int]:
    """
    Rerank indices by a weighted combo:
      combined = alpha * vector_score + (1-alpha) * lexical_score
    Returns indices sorted by combined desc.
    """
    if len(texts) != len(vector_scores):
        raise ValueError("texts and vector_scores length mismatch")

    items: list[RerankedItem] = []
    for i, (t, vs) in enumerate(zip(texts, vector_scores, strict=True)):
        ls = _lexical_score(question, t)
        combined = alpha * float(vs) + (1.0 - alpha) * float(ls)
        items.append(RerankedItem(index=i, combined_score=combined))

    items.sort(key=lambda x: x.combined_score, reverse=True)
    return [x.index for x in items]
