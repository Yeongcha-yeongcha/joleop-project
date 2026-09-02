"""add review card types

Revision ID: 20260902_0008
Revises: 20260902_0007
Create Date: 2026-09-02 00:08:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260902_0008"
down_revision: str | None = "20260902_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'review_card_type') THEN
                CREATE TYPE review_card_type AS ENUM ('WORD', 'SENTENCE', 'CHAT');
            END IF;
        END $$;
        """
    )
    op.execute(
        "ALTER TABLE review_cards ADD COLUMN IF NOT EXISTS card_type review_card_type NOT NULL DEFAULT 'SENTENCE'"
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_review_cards_card_type ON review_cards (card_type)")
    op.execute("ALTER TABLE review_cards DROP CONSTRAINT IF EXISTS uq_review_cards_profile_book_chapter_question")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'uq_review_cards_profile_book_chapter_question'
            ) THEN
                ALTER TABLE review_cards
                ADD CONSTRAINT uq_review_cards_profile_book_chapter_question
                UNIQUE (profile_id, book_id, chapter_number, card_type, source_question_id);
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE review_cards DROP CONSTRAINT IF EXISTS uq_review_cards_profile_book_chapter_question")
    op.execute(
        """
        ALTER TABLE review_cards
        ADD CONSTRAINT uq_review_cards_profile_book_chapter_question
        UNIQUE (profile_id, book_id, chapter_number, source_question_id)
        """
    )
    op.execute("DROP INDEX IF EXISTS ix_review_cards_card_type")
    op.execute("ALTER TABLE review_cards DROP COLUMN IF EXISTS card_type")
    op.execute("DROP TYPE IF EXISTS review_card_type")
