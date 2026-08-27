from difflib import SequenceMatcher


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
    def evaluate(self, *, instruction: str, sentence: str | None, transcript: str) -> dict:
        score = 88 if transcript.strip() else 0
        passed = score >= 60
        feedback = (
            f"Great! {transcript.strip()}"
            if passed
            else "조금 더 자세히 말해볼까요?"
        )
        return {"score": score, "passed": passed, "feedback": feedback}
