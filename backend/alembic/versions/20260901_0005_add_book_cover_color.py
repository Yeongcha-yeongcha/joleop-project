"""add book cover color

Revision ID: 20260901_0005
Revises: 20260829_0005
Create Date: 2026-09-01 00:05:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260901_0005"
down_revision: str | None = "20260829_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("books", sa.Column("cover_color", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("books", "cover_color")
