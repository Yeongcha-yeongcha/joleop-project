from pydantic import BaseModel, Field


class StartLearningSessionRequest(BaseModel):
    chapter_number: int = Field(1, alias="chapterNumber", ge=1)
    restart: bool = False


class ReadingProgressRequest(BaseModel):
    current_step: int = Field(alias="currentStep", ge=1)


class QuestionProgressRequest(BaseModel):
    question_id: int = Field(alias="questionId", ge=1)
