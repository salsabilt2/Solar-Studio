"""roof_space

Revision ID: 457de0f69e78
Revises: cd9e08b0d34c
Create Date: 2026-10-17 01:06:21.545506
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "457de0f69e78"
down_revision: str | Sequence[str] | None = "cd9e08b0d34c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("setups", sa.Column("roof_area_m2", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("setups", "roof_area_m2")
