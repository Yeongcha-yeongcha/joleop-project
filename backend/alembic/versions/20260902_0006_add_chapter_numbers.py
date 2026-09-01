"""add chapter numbers to learning content

Revision ID: 20260902_0006
Revises: 20260901_0005
Create Date: 2026-09-02 00:06:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260902_0006"
down_revision: str | None = "20260901_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE reading_chunks ADD COLUMN IF NOT EXISTS chapter_number INTEGER NOT NULL DEFAULT 1")
    op.execute("ALTER TABLE repeat_questions ADD COLUMN IF NOT EXISTS chapter_number INTEGER NOT NULL DEFAULT 1")
    op.execute("ALTER TABLE description_questions ADD COLUMN IF NOT EXISTS chapter_number INTEGER NOT NULL DEFAULT 1")
    op.execute("ALTER TABLE roleplay_missions ADD COLUMN IF NOT EXISTS chapter_number INTEGER NOT NULL DEFAULT 1")
    op.execute("ALTER TABLE learning_sessions ADD COLUMN IF NOT EXISTS chapter_number INTEGER NOT NULL DEFAULT 1")

    op.execute("ALTER TABLE reading_chunks DROP CONSTRAINT IF EXISTS uq_reading_chunks_book_step")
    op.execute("ALTER TABLE repeat_questions DROP CONSTRAINT IF EXISTS uq_repeat_questions_book_step")
    op.execute("ALTER TABLE description_questions DROP CONSTRAINT IF EXISTS uq_description_questions_book_step")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'uq_reading_chunks_book_chapter_step'
            ) THEN
                ALTER TABLE reading_chunks
                ADD CONSTRAINT uq_reading_chunks_book_chapter_step
                UNIQUE (book_id, chapter_number, step);
            END IF;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'uq_repeat_questions_book_chapter_step'
            ) THEN
                ALTER TABLE repeat_questions
                ADD CONSTRAINT uq_repeat_questions_book_chapter_step
                UNIQUE (book_id, chapter_number, step);
            END IF;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'uq_description_questions_book_chapter_step'
            ) THEN
                ALTER TABLE description_questions
                ADD CONSTRAINT uq_description_questions_book_chapter_step
                UNIQUE (book_id, chapter_number, step);
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.drop_constraint("uq_description_questions_book_chapter_step", "description_questions", type_="unique")
    op.drop_constraint("uq_repeat_questions_book_chapter_step", "repeat_questions", type_="unique")
    op.drop_constraint("uq_reading_chunks_book_chapter_step", "reading_chunks", type_="unique")
    op.create_unique_constraint("uq_description_questions_book_step", "description_questions", ["book_id", "step"])
    op.create_unique_constraint("uq_repeat_questions_book_step", "repeat_questions", ["book_id", "step"])
    op.create_unique_constraint("uq_reading_chunks_book_step", "reading_chunks", ["book_id", "step"])

    op.drop_column("learning_sessions", "chapter_number")
    op.drop_column("roleplay_missions", "chapter_number")
    op.drop_column("description_questions", "chapter_number")
    op.drop_column("repeat_questions", "chapter_number")
    op.drop_column("reading_chunks", "chapter_number")
