import hashlib
from pathlib import Path

from fastapi import status

from app.core.config import settings
from app.core.exceptions import AppException


class TextToSpeechService:
    normal_rate = "-8%"
    slow_rate = "-38%"
    pitch = "+10Hz"

    async def synthesize(self, *, text: str, slow: bool = False) -> bytes:
        normalized_text = " ".join(text.split())
        if not normalized_text:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="읽어줄 문장이 비어 있습니다.",
                code="EMPTY_TTS_TEXT",
            )

        cache_path = self._cache_path(normalized_text, slow=slow)
        if cache_path.exists() and cache_path.stat().st_size > 0:
            return cache_path.read_bytes()
        cache_path.unlink(missing_ok=True)

        await self._save_edge_tts(normalized_text, cache_path=cache_path, slow=slow)
        if not cache_path.exists() or cache_path.stat().st_size == 0:
            raise AppException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="TTS 음성 파일이 비어 있습니다.",
                code="TTS_EMPTY_AUDIO",
            )
        return cache_path.read_bytes()

    async def _save_edge_tts(self, text: str, *, cache_path: Path, slow: bool) -> None:
        try:
            import edge_tts
        except ImportError as exc:
            raise AppException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="edge-tts 패키지가 설치되어 있지 않습니다.",
                code="TTS_DEPENDENCY_MISSING",
            ) from exc

        rate = self.slow_rate if slow else self.normal_rate
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        communicate = edge_tts.Communicate(
            text,
            settings.EDGE_TTS_VOICE,
            rate=rate,
            pitch=self.pitch,
        )
        try:
            await communicate.save(str(cache_path))
        except Exception as exc:
            cache_path.unlink(missing_ok=True)
            raise AppException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="TTS 음성 생성에 실패했습니다.",
                code="TTS_PROVIDER_ERROR",
            ) from exc

    def _cache_path(self, text: str, *, slow: bool) -> Path:
        cache_key = "|".join(
            [
                settings.TTS_PROVIDER,
                settings.EDGE_TTS_VOICE,
                "slow" if slow else "normal",
                self.slow_rate if slow else self.normal_rate,
                self.pitch,
                text,
            ]
        )
        digest = hashlib.sha256(cache_key.encode("utf-8")).hexdigest()
        return Path(settings.EDGE_TTS_CACHE_DIR) / f"{digest}.mp3"
