"""add energy recharge timestamp

Revision ID: 20260902_0009
Revises: 20260902_0008
Create Date: 2026-09-02 00:09:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260902_0009"
down_revision: str | None = "20260902_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE child_profiles ADD COLUMN IF NOT EXISTS energy_recharged_at TIMESTAMPTZ NOT NULL DEFAULT now()"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE child_profiles DROP COLUMN IF EXISTS energy_recharged_at")
