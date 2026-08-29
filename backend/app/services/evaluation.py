from difflib import SequenceMatcher
import re


class RepeatEvaluationService:
    def evaluate(self, *, target_text: str, transcript: str) -> dict:
        ratio = SequenceMatcher(
            None,
            self.normalize(target_text),
            self.normalize(transcript),
        ).ratio()
        score = round(ratio * 100)
        return {"score": score, "passed": score >= 70}

    @staticmethod
    def normalize(text: str) -> str:
        return " ".join(text.lower().strip().split())


class DescriptionEvaluationService:
    def evaluate(
        self,
        *,
        instruction: str,
        sentence: str | None,
        transcript: str,
        answer_sentence: str | None = None,
        blank_word: str | None = None,
    ) -> dict:
        normalized_transcript = self.normalize(transcript)
        if not normalized_transcript:
            return {
                "score": 0,
                "passed": False,
                "feedback": "조금 더 자세히 말해볼까요?",
            }

        expected = blank_word or answer_sentence or sentence
        if not expected:
            return {"score": 88, "passed": True, "feedback": f"Great! {transcript.strip()}"}

        normalized_expected = self.normalize(expected)
        if blank_word and self._contains_word(normalized_transcript, normalized_expected):
            score = 100
        elif normalized_expected in normalized_transcript:
            score = 95
        else:
            score = round(
                SequenceMatcher(None, normalized_expected, normalized_transcript).ratio() * 100
            )

        passed = score >= 60
        feedback = "Great!" if passed else "모범 답안을 보고 다시 말해볼까요?"
        return {"score": score, "passed": passed, "feedback": feedback}

    @staticmethod
    def normalize(text: str) -> str:
        lowered = text.lower().strip()
        lowered = re.sub(r"[^a-z0-9\s']", " ", lowered)
        return " ".join(lowered.split())

    @staticmethod
    def _contains_word(text: str, word: str) -> bool:
        return bool(re.search(rf"\b{re.escape(word)}\b", text))
