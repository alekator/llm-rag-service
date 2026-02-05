"""create documents and chunks with pgvector

Revision ID: c5e1c3a7c50c
Revises:
Create Date: 2026-02-05 20:29:33.951807

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# NOTE: we create pgvector extension and use raw SQL for VECTOR column to avoid extra deps.
EMBEDDING_DIM = 1536

# revision identifiers, used by Alembic.
revision: str = "c5e1c3a7c50c"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("filename", sa.String(length=512), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="uploaded"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("page", sa.Integer(), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # Add embedding column as pgvector VECTOR(1536)
    op.execute(f"ALTER TABLE chunks ADD COLUMN embedding vector({EMBEDDING_DIM});")

    op.create_index("ix_chunks_document_id", "chunks", ["document_id"])
    op.create_index(
        "ix_chunks_document_id_chunk_index", "chunks", ["document_id", "chunk_index"], unique=True
    )


def downgrade() -> None:
    op.drop_index("ix_chunks_document_id_chunk_index", table_name="chunks")
    op.drop_index("ix_chunks_document_id", table_name="chunks")
    op.drop_table("chunks")
    op.drop_table("documents")
    # optional: keep extension
    # op.execute("DROP EXTENSION IF EXISTS vector;")
