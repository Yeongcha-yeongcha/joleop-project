from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import OnboardingAlreadyCompletedException
from app.models import ChildProfile, Difficulty, OnboardingResult
from app.schemas.onboarding import OnboardingSubmitRequest


class OnboardingService:
    def __init__(self, *, session: AsyncSession) -> None:
        self.session = session

    async def submit(
        self,
        *,
        profile: ChildProfile,
        request: OnboardingSubmitRequest,
    ) -> dict:
        if profile.onboarding_completed:
            raise OnboardingAlreadyCompletedException()

        score = self.calculate_score(request)
        difficulty = self.resolve_difficulty(score)

        profile.difficulty = difficulty
        profile.onboarding_completed = True
        self.session.add(
            OnboardingResult(
                profile_id=profile.profile_id,
                score=score,
                difficulty=difficulty,
                answers=[
                    {"questionId": answer.question_id, "answer": answer.answer}
                    for answer in request.answers
                ],
            )
        )
        await self.session.commit()
        await self.session.refresh(profile)

        return {
            "profileId": profile.profile_id,
            "onboardingScore": score,
            "difficulty": difficulty.value,
            "onboardingCompleted": profile.onboarding_completed,
        }

    @staticmethod
    def calculate_score(request: OnboardingSubmitRequest) -> int:
        return sum(2 for _ in request.answers)

    @staticmethod
    def resolve_difficulty(score: int) -> Difficulty:
        if score <= 6:
            return Difficulty.BEGINNER
        if score <= 12:
            return Difficulty.INTERMEDIATE
        return Difficulty.ADVANCED
