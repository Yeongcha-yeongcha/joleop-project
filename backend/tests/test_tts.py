import pytest

from app.api.v1.tts import TtsRequest, synthesize_tts
from app.models import ChildProfile


class FakeTextToSpeechService:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def synthesize(self, *, text: str, slow: bool = False) -> bytes:
        self.calls.append({"text": text, "slow": slow})
        return b"mp3-bytes"


@pytest.mark.asyncio
async def test_synthesize_tts_returns_mp3_response() -> None:
    service = FakeTextToSpeechService()

    response = await synthesize_tts(
        TtsRequest(text="The lion reads a book.", speed="normal"),
        current_profile=ChildProfile(profile_id=1),
        text_to_speech_service=service,
    )

    assert response.media_type == "audio/mpeg"
    assert response.body == b"mp3-bytes"
    assert service.calls == [{"text": "The lion reads a book.", "slow": False}]


@pytest.mark.asyncio
async def test_synthesize_tts_maps_slow_speed() -> None:
    service = FakeTextToSpeechService()

    await synthesize_tts(
        TtsRequest(text="Read slowly.", speed="slow"),
        current_profile=ChildProfile(profile_id=1),
        text_to_speech_service=service,
    )

    assert service.calls == [{"text": "Read slowly.", "slow": True}]
