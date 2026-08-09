from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AccessTokenExpiredException,
    InvalidRefreshTokenException,
    ParentNotFoundException,
    UnauthorizedException,
)
from app.core.security import (
    ExpiredTokenError,
    TokenError,
    create_parent_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
)
from app.models import AuthTokenType, ChildProfile, Parent, RefreshToken
from app.services.kakao import KakaoService


class AuthService:
    def __init__(
        self,
        *,
        session: AsyncSession,
        kakao_service: KakaoService | None = None,
    ) -> None:
        self.session = session
        self.kakao_service = kakao_service or KakaoService()

    async def kakao_login(
        self,
        *,
        authorization_code: str,
        redirect_uri: str | None = None,
    ) -> dict:
        identity = await self.kakao_service.get_parent_identity(
            authorization_code=authorization_code,
            redirect_uri=redirect_uri,
        )
        kakao_id = identity["kakao_id"]
        nickname = identity.get("nickname")

        result = await self.session.execute(
            select(Parent).where(Parent.kakao_id == kakao_id)
        )
        parent = result.scalar_one_or_none()
        is_new_parent = parent is None

        if parent is None:
            parent = Parent(kakao_id=kakao_id, nickname=nickname)
            self.session.add(parent)
            await self.session.flush()
        elif nickname and not parent.nickname:
            parent.nickname = nickname

        refresh_token = create_refresh_token(parent.parent_id)
        self.session.add(
            RefreshToken(
                parent_id=parent.parent_id,
                token_hash=hash_token(refresh_token),
                expires_at=datetime.now(UTC)
                + timedelta(days=self._refresh_expire_days()),
            )
        )
        await self.session.commit()
        await self.session.refresh(parent)

        return {
            "parentAccessToken": create_parent_access_token(parent.parent_id),
            "refreshToken": refresh_token,
            "isNewParent": is_new_parent,
            "parent": await self.parent_summary(parent),
        }

    async def refresh_parent_access_token(self, *, refresh_token: str) -> dict:
        payload = self._decode_expected_token(refresh_token, AuthTokenType.REFRESH)
        parent_id = int(payload["parentId"])
        token_record = await self._get_active_refresh_token(
            parent_id=parent_id,
            refresh_token=refresh_token,
        )
        if token_record is None:
            raise InvalidRefreshTokenException()

        return {"parentAccessToken": create_parent_access_token(parent_id)}

    async def logout(self, *, refresh_token: str) -> dict:
        payload = self._decode_expected_token(refresh_token, AuthTokenType.REFRESH)
        parent_id = int(payload["parentId"])
        token_record = await self._get_active_refresh_token(
            parent_id=parent_id,
            refresh_token=refresh_token,
        )
        if token_record is None:
            raise InvalidRefreshTokenException()

        token_record.revoked_at = datetime.now(UTC)
        await self.session.commit()
        return {"message": "로그아웃되었습니다."}

    async def get_parent_by_access_token(self, token: str) -> Parent:
        payload = self._decode_expected_token(token, AuthTokenType.PARENT)
        parent_id = int(payload["parentId"])

        result = await self.session.execute(
            select(Parent).where(Parent.parent_id == parent_id)
        )
        parent = result.scalar_one_or_none()
        if parent is None:
            raise ParentNotFoundException()
        return parent

    async def parent_summary(self, parent: Parent, *, include_provider: bool = False) -> dict:
        result = await self.session.execute(
            select(func.count(ChildProfile.profile_id)).where(
                ChildProfile.parent_id == parent.parent_id,
                ChildProfile.deleted_at.is_(None),
            )
        )
        data = {
            "parentId": parent.parent_id,
            "nickname": parent.nickname,
            "profileCount": result.scalar_one(),
        }
        if include_provider:
            data["provider"] = parent.provider
        return data

    async def _get_active_refresh_token(
        self,
        *,
        parent_id: int,
        refresh_token: str,
    ) -> RefreshToken | None:
        result = await self.session.execute(
            select(RefreshToken).where(
                RefreshToken.parent_id == parent_id,
                RefreshToken.token_hash == hash_token(refresh_token),
            )
        )
        token_record = result.scalar_one_or_none()
        if (
            token_record is None
            or token_record.revoked_at is not None
            or token_record.expires_at <= datetime.now(UTC)
        ):
            return None
        return token_record

    def _decode_expected_token(
        self,
        token: str,
        token_type: AuthTokenType,
    ) -> dict:
        try:
            payload = decode_token(token)
        except ExpiredTokenError as exc:
            if token_type == AuthTokenType.REFRESH:
                raise InvalidRefreshTokenException() from exc
            raise AccessTokenExpiredException() from exc
        except TokenError as exc:
            if token_type == AuthTokenType.REFRESH:
                raise InvalidRefreshTokenException() from exc
            raise UnauthorizedException("인증이 필요합니다.") from exc

        if payload.get("tokenType") != token_type.value or not payload.get("parentId"):
            raise UnauthorizedException("인증이 필요합니다.")
        return payload

    @staticmethod
    def _refresh_expire_days() -> int:
        from app.core.config import settings

        return settings.PARENT_REFRESH_TOKEN_EXPIRE_DAYS
