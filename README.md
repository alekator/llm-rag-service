# llm-rag-service

Production-like backend service for Retrieval-Augmented Generation (RAG) over user documents.

## Overview

This service provides an API for:
- uploading documents (PDF / DOCX)
- asynchronous ingestion and processing
- chunking and embedding generation
- vector search using PostgreSQL + pgvector
- answering user questions strictly based on retrieved context
- returning source references
- refusing to answer when no relevant context is found

The project is designed as a real backend service, not a tutorial or demo.

## Tech Stack

- Python 3.11
- FastAPI (async)
- PostgreSQL 16 + pgvector
- SQLAlchemy (async)
- Redis (task queue / background processing)
- OpenAI-compatible LLM & embeddings API
- Alembic (migrations)
- Ruff / mypy / pytest / pre-commit
- Docker & docker-compose

## Architecture

High-level flow:

1. Document upload
2. Asynchronous ingestion pipeline:
   - parsing (PDF / DOCX)
   - chunking with overlap
   - embeddings generation
   - persistence in Postgres
3. Query flow:
   - vector search (pgvector)
   - relevance filtering
   - prompt assembly
   - LLM answer generation based only on retrieved context

## Local Development

### Prerequisites
- Docker
- Python 3.11

### Start infrastructure
```bash
docker compose up -d
```
### Run API
```bash
uvicorn app.main:app --reload
```
### Health check
```bash
curl http://127.0.0.1:8000/api/v1/health
```
### Project Status

🚧 Work in progress.
Current stage: service skeleton + async DB wiring.

Upcoming:
- Alembic migrations
- pgvector schema
- ingestion pipeline
- retrieval & answering
