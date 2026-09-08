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


class ReviewRating(StrEnum):
    AGAIN = "AGAIN"
    GOOD = "GOOD"
    EASY = "EASY"


class ReviewCardType(StrEnum):
    WORD = "WORD"
    SENTENCE = "SENTENCE"
    CHAT = "CHAT"


class ReviewMode(StrEnum):
    SMART_MIX = "SMART_MIX"
    WORD_PLAYGROUND = "WORD_PLAYGROUND"
    SENTENCE_QUEST = "SENTENCE_QUEST"
    STORY_TALK = "STORY_TALK"


class AuthTokenType(StrEnum):
    PARENT = "PARENT"
    PROFILE = "PROFILE"
    REFRESH = "REFRESH"
