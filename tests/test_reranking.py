from app.rag.reranking import RerankedItem, rerank_by_overlap


def test_rerank_overlap_promotes_more_relevant_text() -> None:
    q = "postgres pgvector ivfflat index"

    items = [
        RerankedItem(item="hello world", score=0.9),  # high vector score but irrelevant
        RerankedItem(
            item="pgvector ivfflat index in postgres", score=0.6
        ),  # lower vector, but strong overlap
    ]

    out = rerank_by_overlap(
        question=q,
        items=items,
        get_text=lambda s: s,
        weight=0.5,
    )

    assert out[0].item == "pgvector ivfflat index in postgres"
