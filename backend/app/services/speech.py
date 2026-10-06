import os
import tempfile
from functools import cached_property

import httpx
from fastapi import UploadFile
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.services.audio import AudioValidationService


class SpeechToTextService:
    async def transcribe(self, audio: UploadFile) -> str:
        raise NotImplementedError


class MockSpeechToTextService(SpeechToTextService):
    def __init__(self, *, audio_validation_service: AudioValidationService | None = None) -> None:
        self.audio_validation_service = audio_validation_service or AudioValidationService()

    async def transcribe(self, audio: UploadFile) -> str:
        data = await self.audio_validation_service.read_validated_audio(audio)
        try:
            decoded = data.decode("utf-8").strip()
        except UnicodeDecodeError:
            decoded = ""
        return decoded


class GroqSpeechToTextService(SpeechToTextService):
    def __init__(
        self,
        *,
        audio_validation_service: AudioValidationService | None = None,
        http_client: httpx.AsyncClient | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self.audio_validation_service = audio_validation_service or AudioValidationService()
        self.http_client = http_client
        self.api_key = settings.GROQ_API_KEY if api_key is None else api_key
        self.base_url = settings.GROQ_BASE_URL if base_url is None else base_url
        self.model = settings.GROQ_STT_MODEL if model is None else model

    async def transcribe(self, audio: UploadFile) -> str:
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY is required for Groq speech transcription.")

        data = await self.audio_validation_service.read_validated_audio(audio)
        content_type = (audio.content_type or "audio/webm").split(";", 1)[0].strip().lower()
        filename = audio.filename or f"recording{self._suffix_for(content_type)}"
        form_data = {
            "model": self.model,
            "language": settings.STT_LANGUAGE,
            "response_format": "json",
            "temperature": "0",
        }
        prompt = " ".join(
            part
            for part in (
                settings.GROQ_STT_PROMPT.strip(),
                "Vocabulary spelling: Popo, Toto, Pipi, Gigi, Momo.",
            )
            if part
        )
        if prompt:
            form_data["prompt"] = prompt
        request = {
            "files": {"file": (filename, data, content_type)},
            "data": form_data,
            "headers": {"Authorization": f"Bearer {self.api_key}"},
        }

        if self.http_client is not None:
            response = await self.http_client.post(
                f"{self.base_url.rstrip('/')}/audio/transcriptions",
                **request,
            )
        else:
            async with httpx.AsyncClient(timeout=settings.GROQ_STT_TIMEOUT_SECONDS) as client:
                response = await client.post(
                    f"{self.base_url.rstrip('/')}/audio/transcriptions",
                    **request,
                )

        response.raise_for_status()
        payload = response.json()
        return str(payload.get("text") or "").strip()

    def _suffix_for(self, content_type: str) -> str:
        suffixes = {
            "audio/aac": ".aac",
            "audio/ogg": ".ogg",
            "audio/wav": ".wav",
            "audio/x-wav": ".wav",
            "audio/x-m4a": ".m4a",
            "audio/mpeg": ".mp3",
            "audio/mp4": ".m4a",
            "audio/webm": ".webm",
        }
        return suffixes.get(content_type, ".webm")


class FasterWhisperSpeechToTextService(SpeechToTextService):
    def __init__(self, *, audio_validation_service: AudioValidationService | None = None) -> None:
        self.audio_validation_service = audio_validation_service or AudioValidationService()

    @cached_property
    def model(self):
        from faster_whisper import WhisperModel

        return WhisperModel(
            settings.FASTER_WHISPER_MODEL_SIZE,
            device=settings.FASTER_WHISPER_DEVICE,
            compute_type=settings.FASTER_WHISPER_COMPUTE_TYPE,
        )

    async def transcribe(self, audio: UploadFile) -> str:
        data = await self.audio_validation_service.read_validated_audio(audio)
        suffix = self._suffix_for(audio)
        temp_path = ""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(data)
                temp_path = temp_file.name
            return await run_in_threadpool(self._transcribe_file, temp_path)
        finally:
            if temp_path:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass

    def _transcribe_file(self, file_path: str) -> str:
        segments, _ = self.model.transcribe(
            file_path,
            language=settings.STT_LANGUAGE or None,
            beam_size=settings.FASTER_WHISPER_BEAM_SIZE,
            vad_filter=True,
        )
        return " ".join(segment.text.strip() for segment in segments if segment.text.strip()).strip()

    def _suffix_for(self, audio: UploadFile) -> str:
        filename = audio.filename or ""
        _, ext = os.path.splitext(filename)
        if ext:
            return ext
        suffixes = {
            "audio/wav": ".wav",
            "audio/x-wav": ".wav",
            "audio/mpeg": ".mp3",
            "audio/mp4": ".m4a",
            "audio/webm": ".webm",
        }
        return suffixes.get(audio.content_type or "", ".webm")
