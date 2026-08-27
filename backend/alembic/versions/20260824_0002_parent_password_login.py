"""parent password login

Revision ID: 20260824_0002
Revises: 20260807_0001
Create Date: 2026-08-24 01:30:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260824_0002"
down_revision: str | None = "20260807_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("parents", sa.Column("username", sa.String(), nullable=True))
    op.add_column("parents", sa.Column("password_hash", sa.String(), nullable=True))
    op.create_unique_constraint("uq_parents_username", "parents", ["username"])


def downgrade() -> None:
    op.drop_constraint("uq_parents_username", "parents", type_="unique")
    op.drop_column("parents", "password_hash")
    op.drop_column("parents", "username")
