from fastapi import APIRouter, Depends

from app.api.deps import get_current_profile
from app.models import ChildProfile
from app.schemas.common import success_response

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me/stats")
async def get_my_stats(
    current_profile: ChildProfile = Depends(get_current_profile),
) -> dict:
    max_energy = current_profile.max_energy or 1
    return success_response(
        {
            "streak": current_profile.streak_days,
            "hearts": current_profile.hearts,
            "xpPercent": current_profile.energy / max_energy,
        }
    )
