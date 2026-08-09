from fastapi import APIRouter, Depends

from app.api.deps import get_auth_service, get_current_parent
from app.models import Parent
from app.schemas.common import success_response
from app.services.auth import AuthService

router = APIRouter(prefix="/parents", tags=["Parents"])


@router.get("/me")
async def get_me(
    current_parent: Parent = Depends(get_current_parent),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    return success_response(
        await auth_service.parent_summary(current_parent, include_provider=True)
    )
