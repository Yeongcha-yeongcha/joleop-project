from fastapi import UploadFile

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
