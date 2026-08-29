from enum import StrEnum


class Difficulty(StrEnum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"


class CourseType(StrEnum):
    READING = "READING"
    REPEAT = "REPEAT"
    DESCRIPTION = "DESCRIPTION"
    ROLEPLAY = "ROLEPLAY"


class LearningSessionStatus(StrEnum):
    IN_PROGRESS = "IN_PROGRESS"
    EXITED = "EXITED"
    COMPLETED = "COMPLETED"


class DescriptionQuestionType(StrEnum):
    WORD_GUESS = "WORD_GUESS"
    FILL_BLANK = "FILL_BLANK"
    DESCRIPTION = "DESCRIPTION"
    WHY_QUESTION = "WHY_QUESTION"


class AuthTokenType(StrEnum):
    PARENT = "PARENT"
    PROFILE = "PROFILE"
    REFRESH = "REFRESH"
