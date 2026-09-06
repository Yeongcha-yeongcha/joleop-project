from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AccessTokenExpiredException,
    ForbiddenException,
    InvalidProfilePasswordException,
    ProfileLimitExceededException,
    UnauthorizedException,
)
from app.core.security import (
    ExpiredTokenError,
    TokenError,
    create_profile_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models import AuthTokenType, ChildProfile, Parent
from app.schemas.profile import (
    ProfileCreateRequest,
    ProfilePasswordUpdateRequest,
    ProfileUpdateRequest,
)


class ProfileService:
    def __init__(self, *, session: AsyncSession) -> None:
        self.session = session

    async def list_profiles(self, parent: Parent) -> dict:
        profiles = await self._profiles_for_parent(parent.parent_id)
        return {
            "profiles": [self.profile_list_item(profile) for profile in profiles],
            "maxProfiles": settings.MAX_CHILD_PROFILES_PER_PARENT,
            "profileCount": len(profiles),
        }

    async def create_profile(
        self,
        *,
        parent: Parent,
        request: ProfileCreateRequest,
    ) -> dict:
        count = await self._active_profile_count(parent.parent_id)
        if count >= settings.MAX_CHILD_PROFILES_PER_PARENT:
            raise ProfileLimitExceededException()

        profile = ChildProfile(
            parent_id=parent.parent_id,
            nickname=request.nickname,
            age=request.age,
            password_hash=hash_password(request.profile_password),
            profile_image_id=request.profile_image_id,
            profile_image_url=self.profile_image_url(request.profile_image_id),
            onboarding_completed=False,
            streak_days=0,
            hearts=0,
            energy=5,
            max_energy=5,
        )
        self.session.add(profile)
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(profile)
        return self.profile_detail(profile)

    async def update_profile(
        self,
        *,
        parent: Parent,
        profile_id: int,
        request: ProfileUpdateRequest,
    ) -> dict:
        profile = await self.get_owned_profile(parent.parent_id, profile_id)
        if request.nickname is not None:
            profile.nickname = request.nickname
        if request.age is not None:
            profile.age = request.age
        if request.profile_image_id is not None:
            profile.profile_image_id = request.profile_image_id
            profile.profile_image_url = self.profile_image_url(request.profile_image_id)

        await self.session.commit()
        await self.session.refresh(profile)
        return self.profile_detail(profile)

    async def update_password(
        self,
        *,
        parent: Parent,
        profile_id: int,
        request: ProfilePasswordUpdateRequest,
    ) -> dict:
        profile = await self.get_owned_profile(parent.parent_id, profile_id)
        profile.password_hash = hash_password(request.new_password)
        await self.session.commit()
        return {"profileId": profile.profile_id}

    async def soft_delete_profile(self, *, parent: Parent, profile_id: int) -> dict:
        profile = await self.get_owned_profile(parent.parent_id, profile_id)
        profile.deleted_at = datetime.now(UTC)
        await self.session.commit()
        return {"deletedProfileId": profile.profile_id}

    async def login_profile(
        self,
        *,
        parent: Parent,
        profile_id: int,
        profile_password: str,
    ) -> dict:
        profile = await self.get_owned_profile(parent.parent_id, profile_id)
        if not verify_password(profile_password, profile.password_hash):
            raise InvalidProfilePasswordException()

        return {
            "profileAccessToken": create_profile_access_token(
                parent_id=parent.parent_id,
                profile_id=profile.profile_id,
            ),
            "profile": self.profile_token_profile(profile),
        }

    async def get_profile_by_access_token(self, token: str) -> ChildProfile:
        try:
            payload = decode_token(token)
        except ExpiredTokenError as exc:
            raise AccessTokenExpiredException() from exc
        except TokenError as exc:
            raise UnauthorizedException("인증이 필요합니다.") from exc

        if (
            payload.get("tokenType") != AuthTokenType.PROFILE.value
            or not payload.get("parentId")
            or not payload.get("profileId")
        ):
            raise UnauthorizedException("인증이 필요합니다.")

        profile = await self.get_profile(
            parent_id=int(payload["parentId"]),
            profile_id=int(payload["profileId"]),
        )
        if profile is None:
            raise UnauthorizedException("인증이 필요합니다.")
        return profile

    async def get_owned_profile(self, parent_id: int, profile_id: int) -> ChildProfile:
        profile = await self.get_profile(parent_id=parent_id, profile_id=profile_id)
        if profile is None:
            raise ForbiddenException("해당 프로필에 접근할 수 없습니다.")
        return profile

    async def get_profile(
        self,
        *,
        parent_id: int,
        profile_id: int,
    ) -> ChildProfile | None:
        result = await self.session.execute(
            select(ChildProfile).where(
                ChildProfile.profile_id == profile_id,
                ChildProfile.parent_id == parent_id,
                ChildProfile.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def _profiles_for_parent(self, parent_id: int) -> list[ChildProfile]:
        result = await self.session.execute(
            select(ChildProfile)
            .where(
                ChildProfile.parent_id == parent_id,
                ChildProfile.deleted_at.is_(None),
            )
            .order_by(ChildProfile.profile_id)
        )
        return list(result.scalars().all())

    async def _active_profile_count(self, parent_id: int) -> int:
        result = await self.session.execute(
            select(func.count(ChildProfile.profile_id)).where(
                ChildProfile.parent_id == parent_id,
                ChildProfile.deleted_at.is_(None),
            )
        )
        return int(result.scalar_one())

    @staticmethod
    def profile_image_url(profile_image_id: int | None) -> str | None:
        if profile_image_id is None:
            return None
        return f"{settings.PROFILE_IMAGE_BASE_URL}/{profile_image_id}.png"

    @staticmethod
    def profile_list_item(profile: ChildProfile) -> dict:
        return {
            "profileId": profile.profile_id,
            "nickname": profile.nickname,
            "age": profile.age,
            "profileImageUrl": profile.profile_image_url,
            "passwordEnabled": bool(profile.password_hash),
            "onboardingCompleted": profile.onboarding_completed,
            "difficulty": profile.difficulty.value if profile.difficulty else None,
        }

    def profile_detail(self, profile: ChildProfile) -> dict:
        data = self.profile_list_item(profile)
        data["createdAt"] = (
            profile.created_at.isoformat() if profile.created_at is not None else None
        )
        return data

    def profile_token_profile(self, profile: ChildProfile) -> dict:
        data = self.profile_list_item(profile)
        data.pop("passwordEnabled", None)
        return data
