from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_auth_service, get_current_parent, get_db
from app.models import Parent
from app.schemas.common import success_response
from app.services.auth import AuthService
from app.services.parent_reports import ParentReportService

router = APIRouter(prefix="/parents", tags=["Parents"])


@router.get("/me")
async def get_me(
    current_parent: Parent = Depends(get_current_parent),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    return success_response(
        await auth_service.parent_summary(current_parent, include_provider=True)
    )


@router.get("/profiles/{profileId}/report")
async def get_profile_report(
    profileId: int,
    days: int = Query(7, ge=1, le=31),
    current_parent: Parent = Depends(get_current_parent),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success_response(
        await ParentReportService(session=session).weekly_report(
            parent=current_parent,
            profile_id=profileId,
            days=days,
        )
    )
