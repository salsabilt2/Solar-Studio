"""claim_report_jobs

Revision ID: f193f4b35dea
Revises: 1cc32b859f58
Create Date: 2026-10-17 00:58:45.203969
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f193f4b35dea"
down_revision: str | Sequence[str] | None = "1cc32b859f58"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("reports", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("reports", "started_at")
