from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_profile, get_db
from app.models import ChildProfile, LearningSession, LearningSessionStatus
from app.schemas.common import success_response
from app.services.energy import EnergyService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me/stats")
async def get_my_stats(
    current_profile: ChildProfile = Depends(get_current_profile),
    session: AsyncSession = Depends(get_db),
) -> dict:
    energy = EnergyService().apply_recharge(current_profile)
    attendance_dates = (
        await session.execute(
            select(func.date(LearningSession.completed_at))
            .where(
                LearningSession.profile_id == current_profile.profile_id,
                LearningSession.status == LearningSessionStatus.COMPLETED,
                LearningSession.completed_at.is_not(None),
            )
            .group_by(func.date(LearningSession.completed_at))
            .order_by(func.date(LearningSession.completed_at).desc())
            .limit(30)
        )
    ).scalars().all()
    await session.commit()
    return success_response(
        {
            "streak": current_profile.streak_days,
            "hearts": current_profile.hearts,
            "xpPercent": energy["energy"] / (energy["maxEnergy"] or 1),
            "attendanceDates": [str(day) for day in attendance_dates],
            **energy,
        }
    )
