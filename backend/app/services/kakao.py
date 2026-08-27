import logging

import httpx

from app.core.config import settings
from app.core.exceptions import UnauthorizedException

logger = logging.getLogger(__name__)


class KakaoService:
    async def exchange_code_for_access_token(
        self,
        *,
        authorization_code: str,
        redirect_uri: str | None = None,
    ) -> str:
        if not settings.KAKAO_CLIENT_ID:
            logger.warning("Kakao token exchange skipped: KAKAO_CLIENT_ID is not configured")
            raise UnauthorizedException("카카오 설정이 누락되었습니다.")
        resolved_redirect_uri = redirect_uri or settings.KAKAO_REDIRECT_URI
        if not resolved_redirect_uri:
            logger.warning("Kakao token exchange skipped: KAKAO_REDIRECT_URI is not configured")
            raise UnauthorizedException("카카오 redirect URI 설정이 누락되었습니다.")

        logger.info(
            "[Kakao OAuth] client_id configured: %s, client_secret configured: %s, "
            "redirect_uri: %s, authorization_code received: %s",
            bool(settings.KAKAO_CLIENT_ID),
            bool(settings.KAKAO_CLIENT_SECRET),
            resolved_redirect_uri,
            bool(authorization_code),
        )
        data = self._build_token_request_data(
            authorization_code=authorization_code,
            redirect_uri=resolved_redirect_uri,
        )

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(settings.KAKAO_TOKEN_URL, data=data)

        if response.status_code >= 400:
            self._log_kakao_error(
                stage="token exchange",
                response=response,
            )
            raise UnauthorizedException("카카오 인증에 실패했습니다.")

        access_token = response.json().get("access_token")
        if not access_token:
            raise UnauthorizedException("카카오 토큰 응답이 올바르지 않습니다.")
        return access_token

    async def get_user_info(self, *, access_token: str) -> dict:
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(settings.KAKAO_USER_INFO_URL, headers=headers)

        if response.status_code >= 400:
            self._log_kakao_error(
                stage="user info fetch",
                response=response,
            )
            raise UnauthorizedException("카카오 사용자 정보를 가져오지 못했습니다.")
        return response.json()

    async def get_parent_identity(
        self,
        *,
        authorization_code: str,
        redirect_uri: str | None = None,
    ) -> dict[str, str | None]:
        access_token = await self.exchange_code_for_access_token(
            authorization_code=authorization_code,
            redirect_uri=redirect_uri,
        )
        user_info = await self.get_user_info(access_token=access_token)
        kakao_id = user_info.get("id")
        if kakao_id is None:
            raise UnauthorizedException("카카오 사용자 ID를 찾을 수 없습니다.")

        kakao_account = user_info.get("kakao_account") or {}
        profile = kakao_account.get("profile") or {}
        properties = user_info.get("properties") or {}
        nickname = profile.get("nickname") or properties.get("nickname")

        return {"kakao_id": str(kakao_id), "nickname": nickname}

    @staticmethod
    def _build_token_request_data(
        *,
        authorization_code: str,
        redirect_uri: str,
    ) -> dict[str, str]:
        data = {
            "grant_type": "authorization_code",
            "client_id": settings.KAKAO_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "code": authorization_code,
        }
        if settings.KAKAO_CLIENT_SECRET:
            data["client_secret"] = settings.KAKAO_CLIENT_SECRET
        return data

    @staticmethod
    def _log_kakao_error(*, stage: str, response: httpx.Response) -> None:
        error_code: str | None = None
        error_description: str | None = None
        try:
            body = response.json()
        except ValueError:
            body = {}

        if isinstance(body, dict):
            raw_error = body.get("error") or body.get("code")
            raw_description = body.get("error_description") or body.get("msg")
            error_code = str(raw_error) if raw_error is not None else None
            error_description = (
                str(raw_description) if raw_description is not None else None
            )

        logger.warning(
            "Kakao %s failed: status=%s error=%s description=%s",
            stage,
            response.status_code,
            error_code,
            error_description,
        )
