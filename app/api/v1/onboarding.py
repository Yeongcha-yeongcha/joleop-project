from fastapi import APIRouter, Depends

from app.api.deps import get_current_profile, get_onboarding_service
from app.models import ChildProfile
from app.schemas.common import success_response
from app.schemas.onboarding import OnboardingSubmitRequest
from app.services.onboarding import OnboardingService

router = APIRouter(prefix="/profiles/me/onboarding", tags=["Onboarding"])


@router.post("")
async def submit_onboarding(
    request: OnboardingSubmitRequest,
    current_profile: ChildProfile = Depends(get_current_profile),
    onboarding_service: OnboardingService = Depends(get_onboarding_service),
) -> dict:
    return success_response(
        await onboarding_service.submit(profile=current_profile, request=request)
    )
