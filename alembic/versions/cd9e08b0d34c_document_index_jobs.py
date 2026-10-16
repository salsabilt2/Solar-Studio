"""document_index_jobs

Revision ID: cd9e08b0d34c
Revises: f193f4b35dea
Create Date: 2026-10-17 01:02:39.464400
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "cd9e08b0d34c"
down_revision: str | Sequence[str] | None = "f193f4b35dea"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("status", sa.String(length=24), server_default="pending", nullable=False),
    )
    op.add_column("documents", sa.Column("error", sa.Text(), nullable=True))
    op.add_column(
        "documents", sa.Column("index_started_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.execute(
        "UPDATE documents SET status='ready' WHERE id IN (SELECT DISTINCT document_id FROM document_chunks)"
    )


def downgrade() -> None:
    op.drop_column("documents", "index_started_at")
    op.drop_column("documents", "error")
    op.drop_column("documents", "status")
