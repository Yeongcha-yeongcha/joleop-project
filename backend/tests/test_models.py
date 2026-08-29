from sqlalchemy import UniqueConstraint

from app.db.base import Base
from app.models import (
    AuthTokenType,
    Book,
    ChildProfile,
    CourseType,
    DescriptionQuestion,
    DescriptionQuestionType,
    Difficulty,
    LearningSession,
    LearningSessionStatus,
    Parent,
    ReadingChunk,
    RepeatQuestion,
    RoleplayMission,
    UserBookProgress,
)


def test_all_learning_tables_are_registered() -> None:
    assert sorted(Base.metadata.tables) == [
        "books",
        "child_profiles",
        "description_questions",
        "learning_attempts",
        "learning_sessions",
        "onboarding_results",
        "parents",
        "reading_chunks",
        "refresh_tokens",
        "repeat_questions",
        "roleplay_messages",
        "roleplay_missions",
        "user_book_progress",
    ]


def test_enums_match_service_contract() -> None:
    assert [item.value for item in Difficulty] == [
        "BEGINNER",
        "INTERMEDIATE",
        "ADVANCED",
    ]
    assert [item.value for item in CourseType] == [
        "READING",
        "REPEAT",
        "DESCRIPTION",
        "ROLEPLAY",
    ]
    assert [item.value for item in LearningSessionStatus] == [
        "IN_PROGRESS",
        "EXITED",
        "COMPLETED",
    ]
    assert [item.value for item in DescriptionQuestionType] == [
        "WORD_GUESS",
        "FILL_BLANK",
        "DESCRIPTION",
        "WHY_QUESTION",
    ]
    assert [item.value for item in AuthTokenType] == [
        "PARENT",
        "PROFILE",
        "REFRESH",
    ]


def test_core_relationships_are_configured() -> None:
    assert Parent.child_profiles.property.mapper.class_ is ChildProfile
    assert ChildProfile.learning_sessions.property.mapper.class_ is LearningSession
    assert ChildProfile.user_book_progress.property.mapper.class_ is UserBookProgress
    assert Book.reading_chunks.property.mapper.class_ is ReadingChunk
    assert Book.repeat_questions.property.mapper.class_ is RepeatQuestion
    assert Book.description_questions.property.mapper.class_ is DescriptionQuestion
    assert Book.roleplay_missions.property.mapper.class_ is RoleplayMission


def test_unique_constraints_are_configured() -> None:
    unique_constraints = {
        constraint.name
        for table in Base.metadata.tables.values()
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert {
        "uq_parents_kakao_id",
        "uq_reading_chunks_book_step",
        "uq_repeat_questions_book_step",
        "uq_description_questions_book_step",
        "uq_user_book_progress_profile_book",
    }.issubset(unique_constraints)
