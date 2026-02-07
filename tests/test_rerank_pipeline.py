from __future__ import annotations

from dataclasses import dataclass

from app.rag.answering.rerank import rerank_candidates_overlap


@dataclass(frozen=True)
class FakeChunk:
    chunk_index: int
    text: str


def test_rerank_overlap_changes_order_when_weight_high() -> None:
    q = "postgres pgvector cosine distance"

    # orig scores: first is better by vector score, but second has higher overlap
    c1 = FakeChunk(1, "some unrelated text about cats")
    c2 = FakeChunk(2, "pgvector cosine distance in postgres")

    items = [(c1, 0.9), (c2, 0.3)]

    out = rerank_candidates_overlap(
        question=q,
        items=items,
        get_text=lambda c: c.text,
        weight=1.0,
    )

    assert out[0][0].chunk_index == 2


def test_rerank_overlap_keeps_order_when_weight_zero() -> None:
    q = "postgres pgvector cosine distance"

    c1 = FakeChunk(1, "some unrelated text about cats")
    c2 = FakeChunk(2, "pgvector cosine distance in postgres")

    items = [(c1, 0.9), (c2, 0.3)]

    out = rerank_candidates_overlap(
        question=q,
        items=items,
        get_text=lambda c: c.text,
        weight=0.0,
    )

    assert out[0][0].chunk_index == 1
