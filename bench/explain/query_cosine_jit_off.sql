SET jit = off;
EXPLAIN (ANALYZE, BUFFERS)
SELECT id,
    document_id,
    chunk_index
FROM chunks
WHERE document_id = '0a2ee623-5af2-4e24-b892-c29671de3eb1'
ORDER BY embedding <=> (
        SELECT embedding
        FROM chunks
        WHERE embedding IS NOT NULL
        LIMIT 1
    )
LIMIT 5;
