"""vector_search_index

Revision ID: 73bc1b4c0ac8
Revises: 457de0f69e78
Create Date: 2026-10-17 01:08:05.863438
"""

from collections.abc import Sequence

from alembic import op

revision: str = "73bc1b4c0ac8"
down_revision: str | Sequence[str] | None = "457de0f69e78"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_document_chunks_embedding_hnsw "
            "ON document_chunks USING hnsw (embedding vector_cosine_ops)"
        )


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP INDEX IF EXISTS ix_document_chunks_embedding_hnsw")
