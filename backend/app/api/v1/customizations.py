from fastapi import APIRouter, Depends

from app.api.deps import get_current_profile, get_customization_service
from app.models import ChildProfile
from app.schemas.common import success_response
from app.schemas.customization import AvatarSaveRequest, PopoSaveRequest, ThemeSelectRequest
from app.services.customizations import CustomizationService

router = APIRouter(prefix="/customization", tags=["Customization"])


@router.get("")
async def get_customization(
    current_profile: ChildProfile = Depends(get_current_profile),
    customization_service: CustomizationService = Depends(get_customization_service),
) -> dict:
    return success_response(await customization_service.get(profile=current_profile))


@router.put("/theme")
async def select_theme(
    request: ThemeSelectRequest,
    current_profile: ChildProfile = Depends(get_current_profile),
    customization_service: CustomizationService = Depends(get_customization_service),
) -> dict:
    return success_response(
        await customization_service.select_theme(
            profile=current_profile,
            theme_id=request.theme_id,
        )
    )


@router.put("/popo")
async def save_popo(
    request: PopoSaveRequest,
    current_profile: ChildProfile = Depends(get_current_profile),
    customization_service: CustomizationService = Depends(get_customization_service),
) -> dict:
    return success_response(
        await customization_service.save_popo(
            profile=current_profile,
            selected_popo=request.selected_popo.model_dump(exclude_none=True),
        )
    )


@router.put("/avatar")
async def save_avatar(
    request: AvatarSaveRequest,
    current_profile: ChildProfile = Depends(get_current_profile),
    customization_service: CustomizationService = Depends(get_customization_service),
) -> dict:
    return success_response(
        await customization_service.save_avatar(
            profile=current_profile,
            avatar_index=request.avatar_index,
            profile_image_url=request.profile_image_url,
            profile_color=request.profile_color,
        )
    )
