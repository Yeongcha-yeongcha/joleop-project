from fastapi import APIRouter, Depends

from app.api.deps import (
    get_current_parent,
    get_current_profile,
    get_profile_service,
)
from app.models import ChildProfile, Parent
from app.schemas.common import success_response
from app.schemas.profile import (
    ProfileCreateRequest,
    ProfileLoginRequest,
    ProfilePasswordUpdateRequest,
    ProfileUpdateRequest,
)
from app.services.profiles import ProfileService

router = APIRouter(prefix="/profiles", tags=["Profiles"])
profile_auth_router = APIRouter(prefix="/profile-auth", tags=["Profiles"])


@router.get("")
async def list_profiles(
    current_parent: Parent = Depends(get_current_parent),
    profile_service: ProfileService = Depends(get_profile_service),
) -> dict:
    return success_response(await profile_service.list_profiles(current_parent))


@router.post("")
async def create_profile(
    request: ProfileCreateRequest,
    current_parent: Parent = Depends(get_current_parent),
    profile_service: ProfileService = Depends(get_profile_service),
) -> dict:
    return success_response(
        await profile_service.create_profile(parent=current_parent, request=request)
    )


@router.patch("/{profileId}")
async def update_profile(
    profileId: int,
    request: ProfileUpdateRequest,
    current_parent: Parent = Depends(get_current_parent),
    profile_service: ProfileService = Depends(get_profile_service),
) -> dict:
    return success_response(
        await profile_service.update_profile(
            parent=current_parent,
            profile_id=profileId,
            request=request,
        )
    )


@router.delete("/{profileId}")
async def delete_profile(
    profileId: int,
    current_parent: Parent = Depends(get_current_parent),
    profile_service: ProfileService = Depends(get_profile_service),
) -> dict:
    return success_response(
        await profile_service.soft_delete_profile(
            parent=current_parent,
            profile_id=profileId,
        )
    )


@router.patch("/{profileId}/password")
async def update_profile_password(
    profileId: int,
    request: ProfilePasswordUpdateRequest,
    current_parent: Parent = Depends(get_current_parent),
    profile_service: ProfileService = Depends(get_profile_service),
) -> dict:
    return success_response(
        await profile_service.update_password(
            parent=current_parent,
            profile_id=profileId,
            request=request,
        )
    )


@router.post("/{profileId}/login")
async def login_profile(
    profileId: int,
    request: ProfileLoginRequest,
    current_parent: Parent = Depends(get_current_parent),
    profile_service: ProfileService = Depends(get_profile_service),
) -> dict:
    return success_response(
        await profile_service.login_profile(
            parent=current_parent,
            profile_id=profileId,
            profile_password=request.profile_password,
        )
    )


@profile_auth_router.post("/logout")
async def logout_profile(
    current_profile: ChildProfile = Depends(get_current_profile),
) -> dict:
    return success_response({"message": "프로필 세션이 종료되었습니다."})


@router.get("/me")
async def get_profile_me(
    current_profile: ChildProfile = Depends(get_current_profile),
    profile_service: ProfileService = Depends(get_profile_service),
) -> dict:
    return success_response(profile_service.profile_token_profile(current_profile))
