from pydantic import BaseModel, Field


class OnboardingAnswer(BaseModel):
    question_id: int = Field(alias="questionId", ge=1)
    answer: str = Field(min_length=1, max_length=20)


class OnboardingSubmitRequest(BaseModel):
    answers: list[OnboardingAnswer] = Field(min_length=1)
