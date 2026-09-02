"""add review scheduler

Revision ID: 20260902_0007
Revises: 20260902_0006
Create Date: 2026-09-02 00:07:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260902_0007"
down_revision: str | None = "20260902_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'review_rating') THEN
                CREATE TYPE review_rating AS ENUM ('AGAIN', 'GOOD', 'EASY');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'review_card_type') THEN
                CREATE TYPE review_card_type AS ENUM ('WORD', 'SENTENCE', 'CHAT');
            END IF;
        END $$;
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS review_cards (
            card_id BIGSERIAL PRIMARY KEY,
            profile_id BIGINT NOT NULL REFERENCES child_profiles(profile_id) ON DELETE RESTRICT,
            book_id BIGINT NOT NULL REFERENCES books(book_id) ON DELETE RESTRICT,
            chapter_number INTEGER NOT NULL,
            card_type review_card_type NOT NULL DEFAULT 'SENTENCE',
            source_question_id BIGINT,
            source_sentence TEXT NOT NULL,
            cloze_sentence TEXT NOT NULL,
            keyword VARCHAR NOT NULL,
            memory_strength_days DOUBLE PRECISION NOT NULL DEFAULT 1,
            interval_hours INTEGER NOT NULL DEFAULT 0,
            ease_factor INTEGER NOT NULL DEFAULT 250,
            review_count INTEGER NOT NULL DEFAULT 0,
            lapse_count INTEGER NOT NULL DEFAULT 0,
            last_reviewed_at TIMESTAMPTZ,
            next_review_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_review_cards_profile_book_chapter_question
                UNIQUE (profile_id, book_id, chapter_number, card_type, source_question_id)
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_review_cards_profile_id ON review_cards (profile_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_review_cards_book_id ON review_cards (book_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_review_cards_card_type ON review_cards (card_type)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_review_cards_source_question_id ON review_cards (source_question_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_review_cards_next_review_at ON review_cards (next_review_at)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS review_attempts (
            attempt_id BIGSERIAL PRIMARY KEY,
            card_id BIGINT NOT NULL REFERENCES review_cards(card_id) ON DELETE RESTRICT,
            profile_id BIGINT NOT NULL REFERENCES child_profiles(profile_id) ON DELETE RESTRICT,
            rating review_rating NOT NULL,
            correct BOOLEAN NOT NULL,
            score INTEGER NOT NULL,
            memory_before INTEGER NOT NULL,
            memory_after INTEGER NOT NULL,
            next_review_at TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_review_attempts_card_id ON review_attempts (card_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_review_attempts_profile_id ON review_attempts (profile_id)")


def downgrade() -> None:
    op.drop_index("ix_review_attempts_profile_id", table_name="review_attempts")
    op.drop_index("ix_review_attempts_card_id", table_name="review_attempts")
    op.drop_table("review_attempts")
    op.drop_index("ix_review_cards_next_review_at", table_name="review_cards")
    op.drop_index("ix_review_cards_source_question_id", table_name="review_cards")
    op.drop_index("ix_review_cards_card_type", table_name="review_cards")
    op.drop_index("ix_review_cards_book_id", table_name="review_cards")
    op.drop_index("ix_review_cards_profile_id", table_name="review_cards")
    op.drop_table("review_cards")
    op.execute("DROP TYPE IF EXISTS review_card_type")
    op.execute("DROP TYPE IF EXISTS review_rating")
