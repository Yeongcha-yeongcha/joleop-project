import httpx
import pytest

from app.api import deps
from app.core.config import settings
from app.services.speech import GroqSpeechToTextService


class IPadUploadFile:
    filename = "recording.m4a"
    content_type = "audio/mp4;codecs=mp4a.40.2"

    async def read(self) -> bytes:
        return b"fake-m4a-audio"


@pytest.mark.asyncio
async def test_groq_speech_transcription_uploads_ipad_audio() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["authorization"] = request.headers.get("authorization")
        captured["content_type"] = request.headers.get("content-type")
        captured["body"] = request.content
        return httpx.Response(200, json={"text": "I want to help the little bird!"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = GroqSpeechToTextService(
            http_client=client,
            api_key="test-key",
            base_url="https://api.groq.test/openai/v1",
            model="whisper-large-v3-turbo",
        )
        transcript = await service.transcribe(IPadUploadFile())  # type: ignore[arg-type]

    body = captured["body"]
    assert isinstance(body, bytes)
    assert transcript == "I want to help the little bird!"
    assert captured["url"] == "https://api.groq.test/openai/v1/audio/transcriptions"
    assert captured["authorization"] == "Bearer test-key"
    assert str(captured["content_type"]).startswith("multipart/form-data;")
    assert b'filename="recording.m4a"' in body
    assert b"whisper-large-v3-turbo" in body
    assert b"Character names are Popo, Toto, Pipi, Gigi, and Momo" in body
    assert b"fake-m4a-audio" in body


def test_auto_provider_uses_groq_when_api_key_exists(monkeypatch) -> None:
    monkeypatch.setattr(settings, "STT_PROVIDER", "auto")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-key")
    monkeypatch.setattr(deps, "_speech_to_text_service", None)

    service = deps.get_speech_to_text_service()

    assert isinstance(service, GroqSpeechToTextService)
