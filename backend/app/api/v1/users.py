from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_profile, get_db
from app.core.config import settings
from app.models import Book, ChildProfile, LearningSession, LearningSessionStatus, PointTransaction, ProfileCustomization
from app.schemas.common import success_response
from app.services.attendance import current_learning_streak
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
    attendance_date_strings = [str(day) for day in attendance_dates]
    streak = current_learning_streak(attendance_date_strings)
    return success_response(
        {
            "streak": streak,
            "hearts": current_profile.hearts,
            "xpPercent": energy["energy"] / (energy["maxEnergy"] or 1),
            "attendanceDates": attendance_date_strings,
            **energy,
        }
    )


@router.get("/me/points-history")
async def get_my_points_history(
    current_profile: ChildProfile = Depends(get_current_profile),
    session: AsyncSession = Depends(get_db),
) -> dict:
    transactions = list((
        await session.execute(
            select(PointTransaction)
            .where(PointTransaction.profile_id == current_profile.profile_id)
            .order_by(PointTransaction.created_at.desc(), PointTransaction.transaction_id.desc())
            .limit(40)
        )
    ).scalars().all())
    if transactions:
        return success_response(
            {
                "entries": [
                    {
                        "id": f"points-{transaction.transaction_id}",
                        "type": transaction.transaction_type,
                        "amount": transaction.amount,
                        "occurredAt": transaction.created_at.isoformat(),
                        "label": transaction.label,
                    }
                    for transaction in transactions
                ]
            }
        )

    completed_rows = (
        await session.execute(
            select(LearningSession, Book)
            .join(Book, Book.book_id == LearningSession.book_id)
            .where(
                LearningSession.profile_id == current_profile.profile_id,
                LearningSession.status == LearningSessionStatus.COMPLETED,
                LearningSession.completed_at.is_not(None),
            )
            .order_by(LearningSession.completed_at.desc(), LearningSession.session_id.desc())
            .limit(30)
        )
    ).all()
    customization = await session.scalar(
        select(ProfileCustomization).where(ProfileCustomization.profile_id == current_profile.profile_id)
    )

    entries = [
        {
            "id": f"lesson-{learning_session.session_id}",
            "type": "earned",
            "amount": settings.COMPLETION_REWARD_HEARTS,
            "occurredAt": learning_session.completed_at.isoformat(),
            "label": f"{book.title} Chapter {learning_session.chapter_number}",
        }
        for learning_session, book in completed_rows
    ]
    if customization is not None and (customization.spent_stars or 0) > 0:
        entries.append(
            {
                "id": f"spent-{customization.customization_id}",
                "type": "spent",
                "amount": -(customization.spent_stars or 0),
                "occurredAt": customization.updated_at.isoformat(),
                "label": "Style purchases",
            }
        )
    entries.sort(key=lambda entry: entry["occurredAt"], reverse=True)
    return success_response({"entries": entries[:40]})
