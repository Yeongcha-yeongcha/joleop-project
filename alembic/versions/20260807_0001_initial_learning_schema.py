"""initial learning schema

Revision ID: 20260807_0001
Revises:
Create Date: 2026-08-07 00:01:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260807_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


difficulty_enum = postgresql.ENUM(
    "BEGINNER",
    "INTERMEDIATE",
    "ADVANCED",
    name="difficulty",
    create_type=False,
)
course_type_enum = postgresql.ENUM(
    "READING",
    "REPEAT",
    "DESCRIPTION",
    "ROLEPLAY",
    name="course_type",
    create_type=False,
)
learning_session_status_enum = postgresql.ENUM(
    "IN_PROGRESS",
    "EXITED",
    "COMPLETED",
    name="learning_session_status",
    create_type=False,
)
description_question_type_enum = postgresql.ENUM(
    "FILL_BLANK",
    "DESCRIPTION",
    "WHY_QUESTION",
    name="description_question_type",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    difficulty_enum.create(bind, checkfirst=True)
    course_type_enum.create(bind, checkfirst=True)
    learning_session_status_enum.create(bind, checkfirst=True)
    description_question_type_enum.create(bind, checkfirst=True)

    op.create_table(
        "parents",
        sa.Column("parent_id", sa.BigInteger(), primary_key=True),
        sa.Column("kakao_id", sa.String(), nullable=False),
        sa.Column("nickname", sa.String(), nullable=True),
        sa.Column("provider", sa.String(), server_default=sa.text("'KAKAO'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("kakao_id", name="uq_parents_kakao_id"),
    )

    op.create_table(
        "books",
        sa.Column("book_id", sa.BigInteger(), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("lesson_name", sa.String(), nullable=True),
        sa.Column("difficulty", difficulty_enum, nullable=False),
        sa.Column("cover_image_url", sa.String(), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "child_profiles",
        sa.Column("profile_id", sa.BigInteger(), primary_key=True),
        sa.Column("parent_id", sa.BigInteger(), nullable=False),
        sa.Column("nickname", sa.String(), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("profile_image_id", sa.Integer(), nullable=True),
        sa.Column("profile_image_url", sa.String(), nullable=True),
        sa.Column("difficulty", difficulty_enum, nullable=True),
        sa.Column("onboarding_completed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("streak_days", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("hearts", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("energy", sa.Integer(), server_default=sa.text("5"), nullable=False),
        sa.Column("max_energy", sa.Integer(), server_default=sa.text("5"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["parent_id"], ["parents.parent_id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_child_profiles_parent_id", "child_profiles", ["parent_id"])

    op.create_table(
        "onboarding_results",
        sa.Column("onboarding_result_id", sa.BigInteger(), primary_key=True),
        sa.Column("profile_id", sa.BigInteger(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("difficulty", difficulty_enum, nullable=False),
        sa.Column("answers", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["child_profiles.profile_id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_onboarding_results_profile_id", "onboarding_results", ["profile_id"])

    op.create_table(
        "reading_chunks",
        sa.Column("chunk_id", sa.BigInteger(), primary_key=True),
        sa.Column("book_id", sa.BigInteger(), nullable=False),
        sa.Column("step", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("image_url", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["book_id"], ["books.book_id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("book_id", "step", name="uq_reading_chunks_book_step"),
    )
    op.create_index("ix_reading_chunks_book_id", "reading_chunks", ["book_id"])

    op.create_table(
        "repeat_questions",
        sa.Column("question_id", sa.BigInteger(), primary_key=True),
        sa.Column("book_id", sa.BigInteger(), nullable=False),
        sa.Column("step", sa.Integer(), nullable=False),
        sa.Column("target_text", sa.Text(), nullable=False),
        sa.Column("image_url", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["book_id"], ["books.book_id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("book_id", "step", name="uq_repeat_questions_book_step"),
    )
    op.create_index("ix_repeat_questions_book_id", "repeat_questions", ["book_id"])

    op.create_table(
        "description_questions",
        sa.Column("question_id", sa.BigInteger(), primary_key=True),
        sa.Column("book_id", sa.BigInteger(), nullable=False),
        sa.Column("step", sa.Integer(), nullable=False),
        sa.Column("question_type", description_question_type_enum, nullable=False),
        sa.Column("instruction", sa.Text(), nullable=False),
        sa.Column("sentence", sa.Text(), nullable=True),
        sa.Column("image_url", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["book_id"], ["books.book_id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("book_id", "step", name="uq_description_questions_book_step"),
    )
    op.create_index("ix_description_questions_book_id", "description_questions", ["book_id"])

    op.create_table(
        "roleplay_missions",
        sa.Column("mission_id", sa.BigInteger(), primary_key=True),
        sa.Column("book_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("character_name", sa.String(), nullable=False),
        sa.Column("character_image_url", sa.String(), nullable=True),
        sa.Column("opening_message", sa.Text(), nullable=False),
        sa.Column("required_turns", sa.Integer(), server_default=sa.text("3"), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["books.book_id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_roleplay_missions_book_id", "roleplay_missions", ["book_id"])

    op.create_table(
        "user_book_progress",
        sa.Column("progress_id", sa.BigInteger(), primary_key=True),
        sa.Column("profile_id", sa.BigInteger(), nullable=False),
        sa.Column("book_id", sa.BigInteger(), nullable=False),
        sa.Column("progress", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("completed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("unlocked", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("last_studied_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["profile_id"], ["child_profiles.profile_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["book_id"], ["books.book_id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("profile_id", "book_id", name="uq_user_book_progress_profile_book"),
    )
    op.create_index("ix_user_book_progress_profile_id", "user_book_progress", ["profile_id"])
    op.create_index("ix_user_book_progress_book_id", "user_book_progress", ["book_id"])

    op.create_table(
        "learning_sessions",
        sa.Column("session_id", sa.BigInteger(), primary_key=True),
        sa.Column("profile_id", sa.BigInteger(), nullable=False),
        sa.Column("book_id", sa.BigInteger(), nullable=False),
        sa.Column("status", learning_session_status_enum, nullable=False),
        sa.Column("current_course", course_type_enum, nullable=False),
        sa.Column("current_course_number", sa.Integer(), nullable=False),
        sa.Column("current_step", sa.Integer(), nullable=False),
        sa.Column("total_progress", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("total_score", sa.Integer(), nullable=True),
        sa.Column("stars", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_studied_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["profile_id"], ["child_profiles.profile_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["book_id"], ["books.book_id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_learning_sessions_profile_id", "learning_sessions", ["profile_id"])
    op.create_index("ix_learning_sessions_book_id", "learning_sessions", ["book_id"])

    op.create_table(
        "learning_attempts",
        sa.Column("attempt_id", sa.BigInteger(), primary_key=True),
        sa.Column("session_id", sa.BigInteger(), nullable=False),
        sa.Column("course_type", course_type_enum, nullable=False),
        sa.Column("question_id", sa.BigInteger(), nullable=False),
        sa.Column("transcript", sa.Text(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["learning_sessions.session_id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_learning_attempts_session_id", "learning_attempts", ["session_id"])

    op.create_table(
        "roleplay_messages",
        sa.Column("message_id", sa.BigInteger(), primary_key=True),
        sa.Column("session_id", sa.BigInteger(), nullable=False),
        sa.Column("mission_id", sa.BigInteger(), nullable=False),
        sa.Column("turn", sa.Integer(), nullable=False),
        sa.Column("user_transcript", sa.Text(), nullable=False),
        sa.Column("character_response", sa.Text(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("mission_completed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["learning_sessions.session_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["mission_id"], ["roleplay_missions.mission_id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_roleplay_messages_session_id", "roleplay_messages", ["session_id"])
    op.create_index("ix_roleplay_messages_mission_id", "roleplay_messages", ["mission_id"])

    op.create_table(
        "refresh_tokens",
        sa.Column("refresh_token_id", sa.BigInteger(), primary_key=True),
        sa.Column("parent_id", sa.BigInteger(), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["parents.parent_id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_refresh_tokens_parent_id", "refresh_tokens", ["parent_id"])


def downgrade() -> None:
    op.drop_index("ix_refresh_tokens_parent_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_index("ix_roleplay_messages_mission_id", table_name="roleplay_messages")
    op.drop_index("ix_roleplay_messages_session_id", table_name="roleplay_messages")
    op.drop_table("roleplay_messages")
    op.drop_index("ix_learning_attempts_session_id", table_name="learning_attempts")
    op.drop_table("learning_attempts")
    op.drop_index("ix_learning_sessions_book_id", table_name="learning_sessions")
    op.drop_index("ix_learning_sessions_profile_id", table_name="learning_sessions")
    op.drop_table("learning_sessions")
    op.drop_index("ix_user_book_progress_book_id", table_name="user_book_progress")
    op.drop_index("ix_user_book_progress_profile_id", table_name="user_book_progress")
    op.drop_table("user_book_progress")
    op.drop_index("ix_roleplay_missions_book_id", table_name="roleplay_missions")
    op.drop_table("roleplay_missions")
    op.drop_index("ix_description_questions_book_id", table_name="description_questions")
    op.drop_table("description_questions")
    op.drop_index("ix_repeat_questions_book_id", table_name="repeat_questions")
    op.drop_table("repeat_questions")
    op.drop_index("ix_reading_chunks_book_id", table_name="reading_chunks")
    op.drop_table("reading_chunks")
    op.drop_index("ix_onboarding_results_profile_id", table_name="onboarding_results")
    op.drop_table("onboarding_results")
    op.drop_index("ix_child_profiles_parent_id", table_name="child_profiles")
    op.drop_table("child_profiles")
    op.drop_table("books")
    op.drop_table("parents")

    description_question_type_enum.drop(op.get_bind(), checkfirst=True)
    learning_session_status_enum.drop(op.get_bind(), checkfirst=True)
    course_type_enum.drop(op.get_bind(), checkfirst=True)
    difficulty_enum.drop(op.get_bind(), checkfirst=True)
