"""add profile customizations

Revision ID: 20260903_0010
Revises: 20260902_0009
Create Date: 2026-09-03 00:10:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260903_0010"
down_revision: str | None = "20260902_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS profile_customizations (
            customization_id BIGSERIAL PRIMARY KEY,
            profile_id BIGINT NOT NULL REFERENCES child_profiles(profile_id) ON DELETE RESTRICT,
            selected_theme_id VARCHAR NOT NULL DEFAULT 'cream-book-room',
            unlocked_theme_ids JSONB NOT NULL DEFAULT '["cream-book-room"]'::jsonb,
            selected_popo JSONB NOT NULL DEFAULT '{}'::jsonb,
            unlocked_popo_item_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
            unlocked_avatar_indices JSONB NOT NULL DEFAULT '[0]'::jsonb,
            profile_color VARCHAR,
            spent_stars INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_profile_customizations_profile_id UNIQUE (profile_id)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_profile_customizations_profile_id ON profile_customizations(profile_id)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS profile_customizations")
