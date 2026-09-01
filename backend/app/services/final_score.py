from statistics import mean

from app.core.exceptions import ResultNotAvailableException
from app.models import CourseType, LearningAttempt, RoleplayMessage


class FinalScoreService:
    def calculate(
        self,
        *,
        attempts: list[LearningAttempt],
        roleplay_messages: list[RoleplayMessage],
    ) -> dict:
        repeat_scores = [
            attempt.score
            for attempt in attempts
            if attempt.course_type == CourseType.REPEAT
        ]
        description_scores = [
            attempt.score
            for attempt in attempts
            if attempt.course_type == CourseType.DESCRIPTION
        ]
        roleplay_scores = [
            message.score
            for message in roleplay_messages
            if message.score is not None
        ]
        roleplay_completed = any(message.mission_completed for message in roleplay_messages)
        if (
            not repeat_scores
            or not description_scores
            or not roleplay_scores
            or not roleplay_completed
        ):
            raise ResultNotAvailableException()

        total_score = round(
            mean(
                [
                    mean(repeat_scores),
                    mean(description_scores),
                    mean(roleplay_scores),
                ]
            )
        )
        return {"totalScore": total_score, "stars": self.stars(total_score)}

    @staticmethod
    def stars(score: int) -> int:
        if score <= 39:
            return 0
        if score <= 59:
            return 1
        if score <= 79:
            return 2
        return 3
