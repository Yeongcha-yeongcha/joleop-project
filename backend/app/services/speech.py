import os
import tempfile
from functools import cached_property

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
