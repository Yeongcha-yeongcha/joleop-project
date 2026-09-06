from difflib import SequenceMatcher
import re

from app.models import RoleplayMission


class RoleplayService:
    async def respond(
        self,
        *,
        mission: RoleplayMission,
        transcript: str,
        turn: int,
    ) -> dict:
        raise NotImplementedError


class MockRoleplayService(RoleplayService):
    async def respond(
        self,
        *,
        mission: RoleplayMission,
        transcript: str,
        turn: int,
    ) -> dict:
        score = self._score_response(mission=mission, transcript=transcript)
        if score >= 70:
            text = "Thank you! That helps a lot."
        else:
            hints = mission.hint_sequence or ["Can you say it another way?"]
            hint = hints[min(turn - 1, len(hints) - 1)]
            text = hint
        return {
            "speaker": mission.character_name.upper(),
            "text": text,
            "score": score,
        }

    def _score_response(self, *, mission: RoleplayMission, transcript: str) -> int:
        normalized_transcript = self._normalize(transcript)
        if not normalized_transcript:
            return 0
        unsafe_words = {"hit", "kill", "hate", "shut up"}
        if any(word in normalized_transcript for word in unsafe_words):
            return 20

        candidates = [
            mission.model_answer,
            *(mission.similar_answers or []),
            mission.player_goal,
        ]
        candidates = [self._normalize(candidate) for candidate in candidates if candidate]
        if not candidates:
            return 90

        best_ratio = max(
            SequenceMatcher(None, candidate, normalized_transcript).ratio()
            for candidate in candidates
        )
        token_overlap = max(
            self._token_overlap(candidate, normalized_transcript)
            for candidate in candidates
        )
        return round(max(best_ratio, token_overlap) * 100)

    @staticmethod
    def _normalize(text: str) -> str:
        lowered = text.lower().strip()
        lowered = re.sub(r"[^a-z0-9\s']", " ", lowered)
        return " ".join(lowered.split())

    @staticmethod
    def _token_overlap(expected: str, actual: str) -> float:
        expected_tokens = set(expected.split())
        actual_tokens = set(actual.split())
        if not expected_tokens:
            return 0
        return len(expected_tokens & actual_tokens) / len(expected_tokens)
