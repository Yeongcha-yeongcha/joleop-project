from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import (
    CourseType,
    DescriptionQuestionType,
    Difficulty,
    LearningSessionStatus,
)

bigint_pk = BigInteger().with_variant(Integer, "sqlite")
bigint_fk = BigInteger().with_variant(Integer, "sqlite")


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class UpdatedTimestampMixin(TimestampMixin):
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


difficulty_enum = Enum(Difficulty, name="difficulty")
course_type_enum = Enum(CourseType, name="course_type")
learning_session_status_enum = Enum(
    LearningSessionStatus,
    name="learning_session_status",
)
description_question_type_enum = Enum(
    DescriptionQuestionType,
    name="description_question_type",
)


class Parent(UpdatedTimestampMixin, Base):
    __tablename__ = "parents"
    __table_args__ = (
        UniqueConstraint("kakao_id", name="uq_parents_kakao_id"),
        UniqueConstraint("username", name="uq_parents_username"),
    )

    parent_id: Mapped[int] = mapped_column(bigint_pk, primary_key=True)
    kakao_id: Mapped[str] = mapped_column(String, nullable=False)
    username: Mapped[str | None] = mapped_column(String)
    password_hash: Mapped[str | None] = mapped_column(String)
    nickname: Mapped[str | None] = mapped_column(String)
    provider: Mapped[str] = mapped_column(
        String,
        server_default=text("'KAKAO'"),
        nullable=False,
    )

    child_profiles: Mapped[list["ChildProfile"]] = relationship(
        back_populates="parent",
        passive_deletes=True,
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="parent",
        passive_deletes=True,
    )


class ChildProfile(UpdatedTimestampMixin, Base):
    __tablename__ = "child_profiles"

    profile_id: Mapped[int] = mapped_column(bigint_pk, primary_key=True)
    parent_id: Mapped[int] = mapped_column(
        bigint_fk,
        ForeignKey("parents.parent_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    nickname: Mapped[str] = mapped_column(String, nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    profile_image_id: Mapped[int | None] = mapped_column(Integer)
    profile_image_url: Mapped[str | None] = mapped_column(String)
    difficulty: Mapped[Difficulty | None] = mapped_column(difficulty_enum)
    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean,
        server_default=text("false"),
        nullable=False,
    )
    streak_days: Mapped[int] = mapped_column(
        Integer,
        server_default=text("0"),
        nullable=False,
    )
    hearts: Mapped[int] = mapped_column(
        Integer,
        server_default=text("0"),
        nullable=False,
    )
    energy: Mapped[int] = mapped_column(
        Integer,
        server_default=text("5"),
        nullable=False,
    )
    max_energy: Mapped[int] = mapped_column(
        Integer,
        server_default=text("5"),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    parent: Mapped[Parent] = relationship(back_populates="child_profiles")
    onboarding_results: Mapped[list["OnboardingResult"]] = relationship(
        back_populates="profile",
        passive_deletes=True,
    )
    learning_sessions: Mapped[list["LearningSession"]] = relationship(
        back_populates="profile",
        passive_deletes=True,
    )
    user_book_progress: Mapped[list["UserBookProgress"]] = relationship(
        back_populates="profile",
        passive_deletes=True,
    )


class OnboardingResult(TimestampMixin, Base):
    __tablename__ = "onboarding_results"

    onboarding_result_id: Mapped[int] = mapped_column(bigint_pk, primary_key=True)
    profile_id: Mapped[int] = mapped_column(
        bigint_fk,
        ForeignKey("child_profiles.profile_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    difficulty: Mapped[Difficulty] = mapped_column(difficulty_enum, nullable=False)
    answers: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    profile: Mapped[ChildProfile] = relationship(back_populates="onboarding_results")


class Book(TimestampMixin, Base):
    __tablename__ = "books"

    book_id: Mapped[int] = mapped_column(bigint_pk, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    lesson_name: Mapped[str | None] = mapped_column(String)
    difficulty: Mapped[Difficulty] = mapped_column(difficulty_enum, nullable=False)
    cover_image_url: Mapped[str | None] = mapped_column(String)
    display_order: Mapped[int | None] = mapped_column(Integer)

    reading_chunks: Mapped[list["ReadingChunk"]] = relationship(
        back_populates="book",
        passive_deletes=True,
        order_by="ReadingChunk.step",
    )
    repeat_questions: Mapped[list["RepeatQuestion"]] = relationship(
        back_populates="book",
        passive_deletes=True,
        order_by="RepeatQuestion.step",
    )
    description_questions: Mapped[list["DescriptionQuestion"]] = relationship(
        back_populates="book",
        passive_deletes=True,
        order_by="DescriptionQuestion.step",
    )
    roleplay_missions: Mapped[list["RoleplayMission"]] = relationship(
        back_populates="book",
        passive_deletes=True,
    )
    user_book_progress: Mapped[list["UserBookProgress"]] = relationship(
        back_populates="book",
        passive_deletes=True,
    )
    learning_sessions: Mapped[list["LearningSession"]] = relationship(
        back_populates="book",
        passive_deletes=True,
    )


class ReadingChunk(Base):
    __tablename__ = "reading_chunks"
    __table_args__ = (UniqueConstraint("book_id", "step", name="uq_reading_chunks_book_step"),)

    chunk_id: Mapped[int] = mapped_column(bigint_pk, primary_key=True)
    book_id: Mapped[int] = mapped_column(
        bigint_fk,
        ForeignKey("books.book_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    step: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String)

    book: Mapped[Book] = relationship(back_populates="reading_chunks")


class RepeatQuestion(Base):
    __tablename__ = "repeat_questions"
    __table_args__ = (UniqueConstraint("book_id", "step", name="uq_repeat_questions_book_step"),)

    question_id: Mapped[int] = mapped_column(bigint_pk, primary_key=True)
    book_id: Mapped[int] = mapped_column(
        bigint_fk,
        ForeignKey("books.book_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    step: Mapped[int] = mapped_column(Integer, nullable=False)
    target_text: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String)

    book: Mapped[Book] = relationship(back_populates="repeat_questions")


class DescriptionQuestion(Base):
    __tablename__ = "description_questions"
    __table_args__ = (
        UniqueConstraint("book_id", "step", name="uq_description_questions_book_step"),
    )

    question_id: Mapped[int] = mapped_column(bigint_pk, primary_key=True)
    book_id: Mapped[int] = mapped_column(
        bigint_fk,
        ForeignKey("books.book_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    step: Mapped[int] = mapped_column(Integer, nullable=False)
    question_type: Mapped[DescriptionQuestionType] = mapped_column(
        description_question_type_enum,
        nullable=False,
    )
    instruction: Mapped[str] = mapped_column(Text, nullable=False)
    sentence: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String)
    page_number: Mapped[int | None] = mapped_column(Integer)
    source_text: Mapped[str | None] = mapped_column(Text)
    blank_word: Mapped[str | None] = mapped_column(String)
    answer_sentence: Mapped[str | None] = mapped_column(Text)
    guide_hint: Mapped[str | None] = mapped_column(Text)

    book: Mapped[Book] = relationship(back_populates="description_questions")


class RoleplayMission(Base):
    __tablename__ = "roleplay_missions"

    mission_id: Mapped[int] = mapped_column(bigint_pk, primary_key=True)
    book_id: Mapped[int] = mapped_column(
        bigint_fk,
        ForeignKey("books.book_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    character_name: Mapped[str] = mapped_column(String, nullable=False)
    character_image_url: Mapped[str | None] = mapped_column(String)
    opening_message: Mapped[str] = mapped_column(Text, nullable=False)
    player_goal: Mapped[str | None] = mapped_column(Text)
    model_answer: Mapped[str | None] = mapped_column(Text)
    similar_answers: Mapped[list[str] | None] = mapped_column(JSONB)
    hint_sequence: Mapped[list[str] | None] = mapped_column(JSONB)
    required_turns: Mapped[int] = mapped_column(
        Integer,
        server_default=text("3"),
        nullable=False,
    )

    book: Mapped[Book] = relationship(back_populates="roleplay_missions")
    roleplay_messages: Mapped[list["RoleplayMessage"]] = relationship(
        back_populates="mission",
        passive_deletes=True,
    )


class UserBookProgress(Base):
    __tablename__ = "user_book_progress"
    __table_args__ = (
        UniqueConstraint("profile_id", "book_id", name="uq_user_book_progress_profile_book"),
    )

    progress_id: Mapped[int] = mapped_column(bigint_pk, primary_key=True)
    profile_id: Mapped[int] = mapped_column(
        bigint_fk,
        ForeignKey("child_profiles.profile_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    book_id: Mapped[int] = mapped_column(
        bigint_fk,
        ForeignKey("books.book_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    progress: Mapped[int] = mapped_column(
        Integer,
        server_default=text("0"),
        nullable=False,
    )
    completed: Mapped[bool] = mapped_column(
        Boolean,
        server_default=text("false"),
        nullable=False,
    )
    unlocked: Mapped[bool] = mapped_column(
        Boolean,
        server_default=text("false"),
        nullable=False,
    )
    last_studied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    profile: Mapped[ChildProfile] = relationship(back_populates="user_book_progress")
    book: Mapped[Book] = relationship(back_populates="user_book_progress")


class LearningSession(Base):
    __tablename__ = "learning_sessions"

    session_id: Mapped[int] = mapped_column(bigint_pk, primary_key=True)
    profile_id: Mapped[int] = mapped_column(
        bigint_fk,
        ForeignKey("child_profiles.profile_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    book_id: Mapped[int] = mapped_column(
        bigint_fk,
        ForeignKey("books.book_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[LearningSessionStatus] = mapped_column(
        learning_session_status_enum,
        nullable=False,
    )
    current_course: Mapped[CourseType] = mapped_column(course_type_enum, nullable=False)
    current_course_number: Mapped[int] = mapped_column(Integer, nullable=False)
    current_step: Mapped[int] = mapped_column(Integer, nullable=False)
    total_progress: Mapped[int] = mapped_column(
        Integer,
        server_default=text("0"),
        nullable=False,
    )
    total_score: Mapped[int | None] = mapped_column(Integer)
    stars: Mapped[int | None] = mapped_column(Integer)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    last_studied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    profile: Mapped[ChildProfile] = relationship(back_populates="learning_sessions")
    book: Mapped[Book] = relationship(back_populates="learning_sessions")
    learning_attempts: Mapped[list["LearningAttempt"]] = relationship(
        back_populates="session",
        passive_deletes=True,
    )
    roleplay_messages: Mapped[list["RoleplayMessage"]] = relationship(
        back_populates="session",
        passive_deletes=True,
    )


class LearningAttempt(TimestampMixin, Base):
    __tablename__ = "learning_attempts"

    attempt_id: Mapped[int] = mapped_column(bigint_pk, primary_key=True)
    session_id: Mapped[int] = mapped_column(
        bigint_fk,
        ForeignKey("learning_sessions.session_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    course_type: Mapped[CourseType] = mapped_column(course_type_enum, nullable=False)
    question_id: Mapped[int] = mapped_column(bigint_fk, nullable=False)
    transcript: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    feedback: Mapped[str | None] = mapped_column(Text)

    session: Mapped[LearningSession] = relationship(back_populates="learning_attempts")


class RoleplayMessage(TimestampMixin, Base):
    __tablename__ = "roleplay_messages"

    message_id: Mapped[int] = mapped_column(bigint_pk, primary_key=True)
    session_id: Mapped[int] = mapped_column(
        bigint_fk,
        ForeignKey("learning_sessions.session_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    mission_id: Mapped[int] = mapped_column(
        bigint_fk,
        ForeignKey("roleplay_missions.mission_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    turn: Mapped[int] = mapped_column(Integer, nullable=False)
    user_transcript: Mapped[str] = mapped_column(Text, nullable=False)
    character_response: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[int | None] = mapped_column(Integer)
    mission_completed: Mapped[bool] = mapped_column(
        Boolean,
        server_default=text("false"),
        nullable=False,
    )

    session: Mapped[LearningSession] = relationship(back_populates="roleplay_messages")
    mission: Mapped[RoleplayMission] = relationship(back_populates="roleplay_messages")


class RefreshToken(TimestampMixin, Base):
    __tablename__ = "refresh_tokens"

    refresh_token_id: Mapped[int] = mapped_column(bigint_pk, primary_key=True)
    parent_id: Mapped[int] = mapped_column(
        bigint_fk,
        ForeignKey("parents.parent_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    parent: Mapped[Parent] = relationship(back_populates="refresh_tokens")
