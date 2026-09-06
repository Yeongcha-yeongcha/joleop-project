from pydantic import BaseModel, Field

from app.models.enums import ReviewMode, ReviewRating


class ReviewAttemptRequest(BaseModel):
    card_id: int = Field(alias="cardId", ge=1)
    rating: ReviewRating
    correct: bool
    score: int = Field(ge=0, le=100)


class ReviewSeedChapterRequest(BaseModel):
    book_id: int = Field(alias="bookId", ge=1)
    chapter_number: int = Field(alias="chapterNumber", ge=1)


class ReviewModeQuery(BaseModel):
    mode: ReviewMode = ReviewMode.SMART_MIX


class StoryTalkMessageRequest(BaseModel):
    card_ids: list[int] = Field(alias="cardIds", min_length=1, max_length=5)
    message: str = Field(min_length=1, max_length=500)
