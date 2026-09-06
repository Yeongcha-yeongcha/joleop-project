from fastapi import APIRouter, Depends
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.api.deps import get_current_profile, get_text_to_speech_service
from app.models import ChildProfile
from app.services.tts import TextToSpeechService

router = APIRouter(prefix="/tts", tags=["Text to Speech"])


class TtsRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)
    speed: str = Field("normal", pattern="^(normal|slow)$")


@router.post("")
async def synthesize_tts(
    request: TtsRequest,
    current_profile: ChildProfile = Depends(get_current_profile),
    text_to_speech_service: TextToSpeechService = Depends(get_text_to_speech_service),
) -> Response:
    _ = current_profile
    audio = await text_to_speech_service.synthesize(
        text=request.text,
        slow=request.speed == "slow",
    )
    return Response(
        content=audio,
        media_type="audio/mpeg",
        headers={"Cache-Control": "public, max-age=604800"},
    )
