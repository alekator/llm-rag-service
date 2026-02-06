# LLM RAG Service (Backend-focused, Production-like)

Production-oriented Retrieval-Augmented Generation (RAG) backend service built with FastAPI, PostgreSQL + pgvector, async workers, and a retrieval-first design.

The project is intentionally designed to:
- look and feel like a real backend service,
- be discussable on LLM / RAG / Backend interviews,
- work without a real OpenAI API key (mock embeddings & LLM fallback),
- demonstrate clean architecture, async pipelines, and performance awareness.

---

## High-level Overview

This service allows you to:

1. Upload documents (PDF / text)
2. Asynchronously ingest them:
   - parse
   - chunk with overlap
   - generate embeddings
   - store vectors in PostgreSQL (pgvector)
3. Query documents via `/query` endpoint:
   - vector similarity search
   - score & return relevant chunks
   - optionally generate an LLM answer (disabled by default)

The system is retrieval-first: even without an LLM, it always returns sources with relevance scores.

---

## Architecture

![RAG Service Architecture](docs/architecture.drawio.png)

High-level architecture of the service showing:
- async document ingestion via Redis + ARQ
- vector storage in PostgreSQL (pgvector)
- retrieval-first query pipeline
- optional LLM integration

Client
→ FastAPI API
→ PostgreSQL (pgvector)
→ Redis (task queue)
→ ARQ worker (ingestion pipeline)

Main components:
- FastAPI (async HTTP API)
- PostgreSQL + pgvector (vector storage)
- Redis + ARQ (background ingestion)
- SQLAlchemy async ORM
- Strict typing (mypy), linting (ruff), pre-commit hooks

---

## Retrieval Pipeline (Core RAG Flow)

1. Embed query
2. Vector similarity search in pgvector (cosine distance)
3. Score normalization
4. Context construction
5. Optional LLM answer generation

If embeddings or LLM are unavailable, the system degrades gracefully:
- no crashes
- retrieval still works
- sources are returned

---

## Embeddings & LLM Strategy (No API Key Required)

This project intentionally supports multiple backends.

Embeddings backends:
- openai — real OpenAI embeddings (requires API key)
- mock — deterministic fake embeddings (default)

Controlled via environment variables:

APP_EMBEDDINGS_BACKEND=mock
APP_EMBEDDINGS_DIM=1536

LLM backends:
- disabled — retrieval-only mode (default)
- openai — real chat completion

This allows:
- full local development
- CI / tests without external dependencies
- honest demonstration of RAG mechanics

---

## Vector Storage (pgvector)

- PostgreSQL extension: pgvector
- Vector column with fixed dimension
- Cosine distance ordering
- Indexed for similarity search

Example query (simplified):

SELECT *
FROM chunks
ORDER BY embedding <=> :query_embedding
LIMIT :k;

---

## Load Testing (hey)

Simple load tests were executed against `/api/v1/query` using hey.

Test command example:

hey -n 200 -c 20 -m POST -T "application/json" -D bench/query.json http://127.0.0.1:8000/api/v1/query

Results (retrieval-only, mock embeddings):

n = 200, c = 20
- Requests/sec: ~300
- Average latency: ~63 ms
- p95 latency: ~252 ms
- p99 latency: ~273 ms

n = 2000, c = 50
- Requests/sec: ~430
- Average latency: ~108 ms
- p95 latency: ~225 ms
- p99 latency: ~308 ms

These results demonstrate:
- stable throughput
- predictable latency
- no blocking I/O in the query path

---

## API Endpoints

Upload document:

POST /api/v1/documents

Get document status:

GET /api/v1/documents/{document_id}

Query document (RAG):

POST /api/v1/query

Example request payload:

{
  "document_id": "UUID",
  "question": "What is this document about?",
  "top_k": 5
}

Example response:

{
  "answer": null,
  "sources": [
    {
      "chunk_index": 1,
      "text": "...",
      "score": 0.82
    }
  ]
}

---

## Running the Project

Requirements:
- Python 3.11
- Docker & docker-compose

Start infrastructure:

docker compose up -d

Run API:

python -m uvicorn app.main:app --reload

Run worker:

python -m arq app.workers.arq_worker.WorkerSettings

---

## Code Quality & Tooling

- ruff — linting & formatting
- mypy — strict typing
- pytest — tests
- pre-commit — enforced locally
- alembic — migrations
- Docker & docker-compose

---

## Why This Project Matters

This is not a toy demo.

It demonstrates:
- real async backend architecture
- vector search in a relational database
- background ingestion pipelines
- graceful degradation without external APIs
- performance awareness and measurement
- production-style code organization

This is the type of system that can realistically evolve into:
- internal knowledge base
- document Q&A service
- support automation backend
- RAG microservice

---

## Roadmap

- Reranking stub (cross-encoder / heuristic)
- EXPLAIN ANALYZE benchmarks for vector queries
- pgvector index tuning
- Architecture diagram (PNG)
- Query caching
- Streaming responses

---

## Disclaimer

LLM integration is intentionally optional.

The project focuses on backend correctness, performance, and architecture rather than direct API usage.

---

Author:
Backend-focused AI / LLM Engineer
