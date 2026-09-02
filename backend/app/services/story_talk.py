import httpx

from app.core.config import settings
from app.models import ReviewCard


class StoryTalkService:
    async def reply(self, *, cards: list[ReviewCard], child_message: str) -> dict:
        context = "\n".join(
            f"- keyword: {card.keyword}; sentence: {card.source_sentence}"
            for card in cards[:5]
        )

        try:
            text = await self._ollama_reply(context=context, child_message=child_message)
        except (httpx.HTTPError, ValueError, KeyError):
            return self._fallback_reply(cards=cards, child_message=child_message)

        if not text:
            return self._fallback_reply(cards=cards, child_message=child_message)

        return {
            "reply": text,
            "source": "OLLAMA",
            "targetWords": self._target_words(cards),
        }

    async def _ollama_reply(self, *, context: str, child_message: str) -> str:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/chat",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "stream": False,
                    "think": False,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are a warm English practice partner for young children. "
                                "Use only the provided story review context. "
                                "Reply in simple English with 1 or 2 short sentences. "
                                "Ask one easy question. Do not include thinking text, markdown, "
                                "Korean, scores, or explanations."
                            ),
                        },
                        {
                            "role": "user",
                            "content": (
                                f"Story review context:\n{context}\n\n"
                                f"Child said: {child_message}"
                            ),
                        },
                    ],
                    "options": {
                        "temperature": 0.5,
                        "num_predict": 80,
                    },
                },
            )
            response.raise_for_status()

        message = response.json().get("message") or {}
        return self._clean_reply(str(message.get("content") or ""))

    def _fallback_reply(self, *, cards: list[ReviewCard], child_message: str) -> dict:
        words = self._target_words(cards)
        word = words[0] if words else "story"
        return {
            "reply": f"Nice answer! Let's use the word {word}. What happened in the story?",
            "source": "MOCK",
            "targetWords": words,
        }

    @staticmethod
    def _target_words(cards: list[ReviewCard]) -> list[str]:
        return list(dict.fromkeys(card.keyword for card in cards if card.keyword))[:5]

    @staticmethod
    def _clean_reply(text: str) -> str:
        cleaned = text.strip()
        while "<think>" in cleaned and "</think>" in cleaned:
            start = cleaned.find("<think>")
            end = cleaned.find("</think>", start) + len("</think>")
            cleaned = (cleaned[:start] + cleaned[end:]).strip()
        return cleaned
