from datetime import UTC, datetime

import pytest
from fastapi.security import HTTPAuthorizationCredentials

from app.api.deps import get_current_parent, get_current_profile
from app.api.v1.profiles import (
    create_profile,
    delete_profile,
    get_profile_me,
    list_profiles,
    login_profile,
    logout_profile,
    update_profile,
    update_profile_password,
)
from app.core.config import settings
from app.core.exceptions import ForbiddenException, InvalidProfilePasswordException, UnauthorizedException
from app.core.security import create_parent_access_token, create_profile_access_token
from app.models import ChildProfile, Parent
from app.schemas.profile import (
    ProfileCreateRequest,
    ProfileLoginRequest,
    ProfilePasswordUpdateRequest,
    ProfileUpdateRequest,
)
from app.services.auth import AuthService
from app.services.profiles import ProfileService


class FakeScalarResult:
    def __init__(self, values):
        self.values = values

    def all(self):
        return self.values


class FakeResult:
    def __init__(self, value=None, values=None):
        self.value = value
        self.values = values

    def scalar_one_or_none(self):
        return self.value

    def scalar_one(self):
        return self.value

    def scalars(self):
        return FakeScalarResult(self.values or [])


class FakeProfileSession:
    def __init__(self) -> None:
        self.parents = [
            Parent(parent_id=10, kakao_id="kakao-10", nickname="Parent 10", provider="KAKAO"),
            Parent(parent_id=20, kakao_id="kakao-20", nickname="Parent 20", provider="KAKAO"),
        ]
        self.child_profiles: list[ChildProfile] = []
        self.next_profile_id = 101

    async def execute(self, statement):
        entity = statement.column_descriptions[0].get("entity")
        params = statement.compile().params
        if entity is Parent:
            return FakeResult(self._parent_by_id(params["parent_id_1"]))
        if entity is ChildProfile:
            if "profile_id_1" in params and "parent_id_1" in params:
                return FakeResult(
                    self._profile_by_id_and_parent(
                        profile_id=params["profile_id_1"],
                        parent_id=params["parent_id_1"],
                    )
                )
            if "parent_id_1" in params:
                profiles = self._profiles_for_parent(params["parent_id_1"])
                if statement.column_descriptions[0]["name"] == "count":
                    return FakeResult(len(profiles))
                return FakeResult(values=profiles)
        raise AssertionError(f"Unexpected query: {statement}")

    def add(self, instance) -> None:
        if isinstance(instance, ChildProfile):
            if instance.profile_id is None:
                instance.profile_id = self.next_profile_id
                self.next_profile_id += 1
            if instance.created_at is None:
                instance.created_at = datetime.now(UTC)
            if instance.updated_at is None:
                instance.updated_at = datetime.now(UTC)
            self.child_profiles.append(instance)
            return
        raise AssertionError(f"Unexpected add: {instance}")

    async def flush(self) -> None:
        return None

    async def commit(self) -> None:
        return None

    async def refresh(self, instance) -> None:
        return None

    def _parent_by_id(self, parent_id: int) -> Parent | None:
        return next((parent for parent in self.parents if parent.parent_id == parent_id), None)

    def _profiles_for_parent(self, parent_id: int) -> list[ChildProfile]:
        return [
            profile
            for profile in self.child_profiles
            if profile.parent_id == parent_id and profile.deleted_at is None
        ]

    def _profile_by_id_and_parent(
        self,
        *,
        profile_id: int,
        parent_id: int,
    ) -> ChildProfile | None:
        return next(
            (
                profile
                for profile in self.child_profiles
                if profile.profile_id == profile_id
                and profile.parent_id == parent_id
                and profile.deleted_at is None
            ),
            None,
        )


@pytest.fixture
def profile_context():
    settings.JWT_SECRET_KEY = "test-secret-at-least-32-bytes-long"
    settings.MAX_CHILD_PROFILES_PER_PARENT = 5
    settings.PROFILE_IMAGE_BASE_URL = "https://cdn.example.com/profiles"
    session = FakeProfileSession()
    return {
        "session": session,
        "parent": session.parents[0],
        "other_parent": session.parents[1],
        "auth_service": AuthService(session=session),
        "profile_service": ProfileService(session=session),
    }


async def create_sample_profile(context, *, password: str = "1234") -> dict:
    return await create_profile(
        ProfileCreateRequest(
            nickname="은정",
            age=8,
            profilePassword=password,
            profileImageId=3,
        ),
        current_parent=context["parent"],
        profile_service=context["profile_service"],
    )


@pytest.mark.asyncio
async def test_profile_create_hashes_password(profile_context) -> None:
    response = await create_sample_profile(profile_context)
    profile = profile_context["session"].child_profiles[0]

    assert response["success"] is True
    assert response["data"]["profileId"] == 101
    assert response["data"]["profileImageUrl"] == "https://cdn.example.com/profiles/3.png"
    assert profile.password_hash != "1234"
    assert profile.password_hash.startswith("$argon2")


@pytest.mark.asyncio
async def test_profile_list(profile_context) -> None:
    await create_sample_profile(profile_context)

    response = await list_profiles(
        current_parent=profile_context["parent"],
        profile_service=profile_context["profile_service"],
    )

    assert response["data"]["maxProfiles"] == 5
    assert response["data"]["profileCount"] == 1
    assert response["data"]["profiles"][0]["passwordEnabled"] is True


@pytest.mark.asyncio
async def test_profile_update(profile_context) -> None:
    await create_sample_profile(profile_context)

    response = await update_profile(
        101,
        ProfileUpdateRequest(nickname="은정이", age=9, profileImageId=4),
        current_parent=profile_context["parent"],
        profile_service=profile_context["profile_service"],
    )

    assert response["data"]["nickname"] == "은정이"
    assert response["data"]["age"] == 9
    assert response["data"]["profileImageUrl"] == "https://cdn.example.com/profiles/4.png"


@pytest.mark.asyncio
async def test_profile_password_update(profile_context) -> None:
    await create_sample_profile(profile_context)

    await update_profile_password(
        101,
        ProfilePasswordUpdateRequest(newPassword="5678"),
        current_parent=profile_context["parent"],
        profile_service=profile_context["profile_service"],
    )

    with pytest.raises(InvalidProfilePasswordException):
        await login_profile(
            101,
            ProfileLoginRequest(profilePassword="1234"),
            current_parent=profile_context["parent"],
            profile_service=profile_context["profile_service"],
        )

    response = await login_profile(
        101,
        ProfileLoginRequest(profilePassword="5678"),
        current_parent=profile_context["parent"],
        profile_service=profile_context["profile_service"],
    )
    assert response["data"]["profileAccessToken"]


@pytest.mark.asyncio
async def test_profile_login_with_correct_password(profile_context) -> None:
    await create_sample_profile(profile_context)

    response = await login_profile(
        101,
        ProfileLoginRequest(profilePassword="1234"),
        current_parent=profile_context["parent"],
        profile_service=profile_context["profile_service"],
    )

    assert response["success"] is True
    assert response["data"]["profile"]["profileId"] == 101
    assert response["data"]["profileAccessToken"]


@pytest.mark.asyncio
async def test_profile_login_with_wrong_password(profile_context) -> None:
    await create_sample_profile(profile_context)

    with pytest.raises(InvalidProfilePasswordException):
        await login_profile(
            101,
            ProfileLoginRequest(profilePassword="0000"),
            current_parent=profile_context["parent"],
            profile_service=profile_context["profile_service"],
        )


@pytest.mark.asyncio
async def test_other_parent_profile_access_is_blocked(profile_context) -> None:
    await create_sample_profile(profile_context)

    with pytest.raises(ForbiddenException):
        await update_profile(
            101,
            ProfileUpdateRequest(nickname="Nope"),
            current_parent=profile_context["other_parent"],
            profile_service=profile_context["profile_service"],
        )

    with pytest.raises(ForbiddenException):
        await login_profile(
            101,
            ProfileLoginRequest(profilePassword="1234"),
            current_parent=profile_context["other_parent"],
            profile_service=profile_context["profile_service"],
        )


@pytest.mark.asyncio
async def test_profile_soft_delete(profile_context) -> None:
    await create_sample_profile(profile_context)

    response = await delete_profile(
        101,
        current_parent=profile_context["parent"],
        profile_service=profile_context["profile_service"],
    )

    assert response["data"] == {"deletedProfileId": 101}
    assert profile_context["session"].child_profiles[0].deleted_at is not None
    list_response = await list_profiles(
        current_parent=profile_context["parent"],
        profile_service=profile_context["profile_service"],
    )
    assert list_response["data"]["profileCount"] == 0


@pytest.mark.asyncio
async def test_parent_and_profile_token_types_are_separated(profile_context) -> None:
    await create_sample_profile(profile_context)
    parent_token = create_parent_access_token(10)
    profile_token = create_profile_access_token(parent_id=10, profile_id=101)

    with pytest.raises(UnauthorizedException):
        await get_current_parent(
            HTTPAuthorizationCredentials(scheme="Bearer", credentials=profile_token),
            auth_service=profile_context["auth_service"],
        )

    with pytest.raises(UnauthorizedException):
        await get_current_profile(
            HTTPAuthorizationCredentials(scheme="Bearer", credentials=parent_token),
            profile_service=profile_context["profile_service"],
        )

    profile = await get_current_profile(
        HTTPAuthorizationCredentials(scheme="Bearer", credentials=profile_token),
        profile_service=profile_context["profile_service"],
    )
    response = await get_profile_me(
        current_profile=profile,
        profile_service=profile_context["profile_service"],
    )
    assert response["data"]["profileId"] == 101

    logout_response = await logout_profile(current_profile=profile)
    assert logout_response["success"] is True
