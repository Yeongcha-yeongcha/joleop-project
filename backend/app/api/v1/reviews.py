from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_profile, get_review_service
from app.models import ChildProfile, ReviewMode
from app.schemas.common import success_response
from app.schemas.review import ReviewAttemptRequest, ReviewSeedChapterRequest, StoryTalkMessageRequest
from app.services.reviews import ReviewService

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
