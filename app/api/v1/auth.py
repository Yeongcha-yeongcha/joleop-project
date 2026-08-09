from fastapi import APIRouter, Depends

from app.api.deps import get_auth_service
from app.schemas.auth import KakaoLoginRequest, LogoutRequest, RefreshTokenRequest
from app.schemas.common import success_response
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/kakao")
async def kakao_login(
    request: KakaoLoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    data = await auth_service.kakao_login(
        authorization_code=request.authorization_code,
        redirect_uri=request.redirect_uri,
    )
    return success_response(data)


@router.post("/refresh")
async def refresh_parent_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    data = await auth_service.refresh_parent_access_token(
        refresh_token=request.refresh_token,
    )
    return success_response(data)


@router.post("/logout")
async def logout(
    request: LogoutRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    data = await auth_service.logout(refresh_token=request.refresh_token)
    return success_response(data)
