import json

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile

from app.api.deps import get_current_profile, get_review_service, get_speech_to_text_service
from app.models import ChildProfile, ReviewMode
from app.schemas.common import success_response
from app.schemas.review import ReviewAttemptRequest, ReviewSeedChapterRequest, StoryTalkMessageRequest
from app.services.reviews import ReviewService
from app.services.speech import SpeechToTextService

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.get("/summary")
async def get_review_summary(
    current_profile: ChildProfile = Depends(get_current_profile),
    review_service: ReviewService = Depends(get_review_service),
) -> dict:
    return success_response(await review_service.summary(profile=current_profile))


@router.get("/due")
async def get_due_reviews(
    limit: int = Query(5, ge=1, le=20),
    mode: ReviewMode = Query(ReviewMode.SMART_MIX),
    current_profile: ChildProfile = Depends(get_current_profile),
    review_service: ReviewService = Depends(get_review_service),
) -> dict:
    return success_response(await review_service.due_cards(profile=current_profile, limit=limit, mode=mode))


@router.get("/story-talk")
async def get_story_talk(
    limit: int = Query(5, ge=1, le=20),
    current_profile: ChildProfile = Depends(get_current_profile),
    review_service: ReviewService = Depends(get_review_service),
) -> dict:
    return success_response(await review_service.story_talk_prompt(profile=current_profile, limit=limit))


@router.post("/story-talk/messages")
async def create_story_talk_message(
    request: StoryTalkMessageRequest,
    current_profile: ChildProfile = Depends(get_current_profile),
    review_service: ReviewService = Depends(get_review_service),
) -> dict:
    return success_response(
        await review_service.story_talk_reply(
            profile=current_profile,
            card_ids=request.card_ids,
            message=request.message,
        )
    )


@router.post("/story-talk/roleplay/messages")
async def create_story_talk_roleplay_message(
    audio: UploadFile = File(...),
    card_id: int = Form(..., alias="cardId"),
    transcript: str | None = Form(default=None),
    history_json: str | None = Form(default=None, alias="historyJson"),
    current_profile: ChildProfile = Depends(get_current_profile),
    review_service: ReviewService = Depends(get_review_service),
    speech_to_text_service: SpeechToTextService = Depends(get_speech_to_text_service),
) -> dict:
    submitted_transcript = transcript if isinstance(transcript, str) else None
    message = (
        submitted_transcript.strip()
        if submitted_transcript and submitted_transcript.strip()
        else await speech_to_text_service.transcribe(audio)
    )
    try:
        history = json.loads(history_json or "[]")
    except json.JSONDecodeError:
        history = []
    return success_response(
        await review_service.story_roleplay_reply(
            profile=current_profile,
            card_id=card_id,
            message=message,
            history=history if isinstance(history, list) else [],
        )
    )


@router.post("/attempts")
async def create_review_attempt(
    request: ReviewAttemptRequest,
    current_profile: ChildProfile = Depends(get_current_profile),
    review_service: ReviewService = Depends(get_review_service),
) -> dict:
    return success_response(
        await review_service.record_attempt(
            profile=current_profile,
            card_id=request.card_id,
            rating=request.rating,
            correct=request.correct,
            score=request.score,
        )
    )


@router.post("/seed-chapter")
async def seed_review_chapter(
    request: ReviewSeedChapterRequest,
    current_profile: ChildProfile = Depends(get_current_profile),
    review_service: ReviewService = Depends(get_review_service),
) -> dict:
    return success_response(
        await review_service.seed_chapter_for_profile(
            profile=current_profile,
            book_id=request.book_id,
            chapter_number=request.chapter_number,
        )
    )
