"""add ai generated content fields

Revision ID: 20260829_0005
Revises: 20260828_0004
Create Date: 2026-08-29 00:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260829_0005"
down_revision: str | None = "20260828_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE description_question_type ADD VALUE IF NOT EXISTS 'WORD_GUESS'")
    json_type = (
        postgresql.JSONB(astext_type=sa.Text())
        if bind.dialect.name == "postgresql"
        else sa.JSON()
    )

    op.add_column("description_questions", sa.Column("page_number", sa.Integer(), nullable=True))
    op.add_column("description_questions", sa.Column("source_text", sa.Text(), nullable=True))
    op.add_column("description_questions", sa.Column("blank_word", sa.String(), nullable=True))
    op.add_column("description_questions", sa.Column("answer_sentence", sa.Text(), nullable=True))
    op.add_column("description_questions", sa.Column("guide_hint", sa.Text(), nullable=True))
    op.add_column("roleplay_missions", sa.Column("player_goal", sa.Text(), nullable=True))
    op.add_column("roleplay_missions", sa.Column("model_answer", sa.Text(), nullable=True))
    op.add_column("roleplay_missions", sa.Column("similar_answers", json_type, nullable=True))
    op.add_column("roleplay_missions", sa.Column("hint_sequence", json_type, nullable=True))


def downgrade() -> None:
    op.drop_column("roleplay_missions", "hint_sequence")
    op.drop_column("roleplay_missions", "similar_answers")
    op.drop_column("roleplay_missions", "model_answer")
    op.drop_column("roleplay_missions", "player_goal")
    op.drop_column("description_questions", "guide_hint")
    op.drop_column("description_questions", "answer_sentence")
    op.drop_column("description_questions", "blank_word")
    op.drop_column("description_questions", "source_text")
    op.drop_column("description_questions", "page_number")
