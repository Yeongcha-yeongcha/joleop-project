from pydantic import BaseModel, Field


class ReadingProgressRequest(BaseModel):
    current_step: int = Field(alias="currentStep", ge=1)


class QuestionProgressRequest(BaseModel):
    question_id: int = Field(alias="questionId", ge=1)
