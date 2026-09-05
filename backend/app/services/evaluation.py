from difflib import SequenceMatcher
import re


class RepeatEvaluationService:
    def evaluate(self, *, target_text: str, transcript: str) -> dict:
        word_results = self.word_results(target_text=target_text, transcript=transcript)
        ratio = SequenceMatcher(
            None,
            self.normalize(target_text),
            self.normalize(transcript),
        ).ratio()
        score = round(ratio * 100)
        if word_results:
            correct_count = sum(1 for result in word_results if result["correct"])
            missed_count = len(word_results) - correct_count
            passed = missed_count <= self.allowed_missed_words(len(word_results))
            score = 100 if passed else round(correct_count / len(word_results) * 100)
            display_word_results = (
                [{**result, "correct": True} for result in word_results]
                if passed
                else word_results
            )
            return {"score": score, "passed": passed, "wordResults": display_word_results}
        return {"score": score, "passed": score >= 70, "wordResults": word_results}

    @staticmethod
    def normalize(text: str) -> str:
        lowered = text.lower().strip()
        lowered = re.sub(r"[^a-z0-9\s']", " ", lowered)
        return " ".join(lowered.split())

    @classmethod
    def word_results(cls, *, target_text: str, transcript: str) -> list[dict]:
        target_words = cls._words(target_text)
        transcript_words = [word for _, word in cls._words(transcript)]
        if not target_words:
            return []

        results = [
            {
                "word": original,
                "normalizedWord": normalized,
                "recognizedWord": None,
                "correct": False,
            }
            for original, normalized in target_words
        ]
        matcher = SequenceMatcher(
            None,
            [word for _, word in target_words],
            transcript_words,
            autojunk=False,
        )

        for tag, target_start, target_end, transcript_start, transcript_end in matcher.get_opcodes():
            if tag == "equal":
                for offset, target_index in enumerate(range(target_start, target_end)):
                    results[target_index]["recognizedWord"] = transcript_words[
                        transcript_start + offset
                    ]
                    results[target_index]["correct"] = True
            elif tag == "replace":
                replaced = transcript_words[transcript_start:transcript_end]
                for offset, target_index in enumerate(range(target_start, target_end)):
                    recognized = replaced[offset] if offset < len(replaced) else None
                    expected = results[target_index]["normalizedWord"]
                    results[target_index]["recognizedWord"] = recognized
                    results[target_index]["correct"] = (
                        recognized is not None
                        and SequenceMatcher(None, expected, recognized).ratio() >= 0.84
                    )

        return results

    @classmethod
    def _words(cls, text: str) -> list:
        return [
            (match.group(0), cls.normalize(match.group(0)))
            for match in re.finditer(r"[A-Za-z0-9']+", text)
        ]

    @staticmethod
    def allowed_missed_words(word_count: int) -> int:
        if word_count >= 5:
            return 2
        if word_count >= 4:
            return 1
        return 0


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
