import pytest
from fastapi.security import HTTPAuthorizationCredentials

from app.api.deps import get_current_parent
from app.api.v1.auth import kakao_login, logout, refresh_parent_token
from app.api.v1.parents import get_me
from app.core.config import settings
from app.core.exceptions import UnauthorizedException
from app.core.security import hash_token
from app.models import ChildProfile, Parent, RefreshToken
from app.schemas.auth import KakaoLoginRequest, LogoutRequest, RefreshTokenRequest
from app.services.auth import AuthService


class FakeResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value

    def scalar_one(self):
        return self.value


class FakeSession:
    def __init__(self) -> None:
        self.parents: list[Parent] = []
        self.child_profiles: list[ChildProfile] = []
        self.refresh_tokens: list[RefreshToken] = []
        self.next_parent_id = 1
        self.next_refresh_token_id = 1

    async def execute(self, statement):
        entity = statement.column_descriptions[0].get("entity")
        params = statement.compile().params
        if entity is Parent:
            if "kakao_id_1" in params:
                return FakeResult(self._parent_by_kakao_id(params["kakao_id_1"]))
            return FakeResult(self._parent_by_id(params["parent_id_1"]))
        if entity is ChildProfile:
            parent_id = params["parent_id_1"]
            count = sum(
                1
                for profile in self.child_profiles
                if profile.parent_id == parent_id and profile.deleted_at is None
            )
            return FakeResult(count)
        if entity is RefreshToken:
            return FakeResult(
                self._refresh_token(
                    parent_id=params["parent_id_1"],
                    token_hash=params["token_hash_1"],
                )
            )
        raise AssertionError(f"Unexpected query: {statement}")

    def add(self, instance) -> None:
        if isinstance(instance, Parent):
            if instance.parent_id is None:
                instance.parent_id = self.next_parent_id
                self.next_parent_id += 1
            if instance.provider is None:
                instance.provider = "KAKAO"
            self.parents.append(instance)
        elif isinstance(instance, RefreshToken):
            if instance.refresh_token_id is None:
                instance.refresh_token_id = self.next_refresh_token_id
                self.next_refresh_token_id += 1
            self.refresh_tokens.append(instance)
        else:
            raise AssertionError(f"Unexpected add: {instance}")

    async def flush(self) -> None:
        return None

    async def commit(self) -> None:
        return None

    async def refresh(self, instance) -> None:
        return None

    def _parent_by_kakao_id(self, kakao_id: str) -> Parent | None:
        return next((parent for parent in self.parents if parent.kakao_id == kakao_id), None)

    def _parent_by_id(self, parent_id: int) -> Parent | None:
        return next((parent for parent in self.parents if parent.parent_id == parent_id), None)

    def _refresh_token(self, *, parent_id: int, token_hash: str) -> RefreshToken | None:
        return next(
            (
                token
                for token in self.refresh_tokens
                if token.parent_id == parent_id and token.token_hash == token_hash
            ),
            None,
        )


class FakeKakaoService:
    kakao_id = "kakao-1"
    nickname = "다은"

    async def get_parent_identity(
        self,
        *,
        authorization_code: str,
        redirect_uri: str | None = None,
    ) -> dict[str, str]:
        return {"kakao_id": self.kakao_id, "nickname": self.nickname}


@pytest.fixture
def auth_service() -> AuthService:
    settings.JWT_SECRET_KEY = "test-secret-at-least-32-bytes-long"
    settings.PARENT_ACCESS_TOKEN_EXPIRE_MINUTES = 60
    settings.PARENT_REFRESH_TOKEN_EXPIRE_DAYS = 14
    return AuthService(session=FakeSession(), kakao_service=FakeKakaoService())


async def run_kakao_login(auth_service: AuthService) -> dict:
    response = await kakao_login(
        KakaoLoginRequest(
            authorizationCode="code",
            redirectUri="https://example.com/oauth/kakao/callback",
        ),
        auth_service=auth_service,
    )
    assert response["success"] is True
    return response["data"]


def test_kakao_login_request_accepts_camel_case_aliases() -> None:
    request = KakaoLoginRequest(
        authorizationCode="code",
        redirectUri="https://example.com/oauth/kakao/callback",
    )

    assert request.authorization_code == "code"
    assert request.redirect_uri == "https://example.com/oauth/kakao/callback"


def test_kakao_login_request_accepts_python_field_names() -> None:
    request = KakaoLoginRequest(
        authorization_code="code",
        redirect_uri="https://example.com/oauth/kakao/callback",
    )

    assert request.authorization_code == "code"
    assert request.redirect_uri == "https://example.com/oauth/kakao/callback"


@pytest.mark.asyncio
async def test_new_kakao_parent_is_created(auth_service: AuthService) -> None:
    data = await run_kakao_login(auth_service)

    assert data["isNewParent"] is True
    assert data["parentAccessToken"]
    assert data["refreshToken"]
    assert data["parent"] == {
        "parentId": 1,
        "nickname": "다은",
        "profileCount": 0,
    }
    assert auth_service.session.refresh_tokens[0].token_hash == hash_token(data["refreshToken"])


@pytest.mark.asyncio
async def test_existing_kakao_parent_logs_in(auth_service: AuthService) -> None:
    first = await run_kakao_login(auth_service)
    second = await run_kakao_login(auth_service)

    assert first["parent"]["parentId"] == second["parent"]["parentId"]
    assert second["isNewParent"] is False


@pytest.mark.asyncio
async def test_invalid_token_is_blocked(auth_service: AuthService) -> None:
    with pytest.raises(UnauthorizedException):
        await get_current_parent(
            HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad-token"),
            auth_service=auth_service,
        )


@pytest.mark.asyncio
async def test_get_parent_me(auth_service: AuthService) -> None:
    login_data = await run_kakao_login(auth_service)
    parent = await auth_service.get_parent_by_access_token(login_data["parentAccessToken"])

    response = await get_me(current_parent=parent, auth_service=auth_service)

    assert response == {
        "success": True,
        "data": {
            "parentId": 1,
            "nickname": "다은",
            "profileCount": 0,
            "provider": "KAKAO",
        },
    }


@pytest.mark.asyncio
async def test_refresh_success(auth_service: AuthService) -> None:
    login_data = await run_kakao_login(auth_service)

    response = await refresh_parent_token(
        RefreshTokenRequest(refreshToken=login_data["refreshToken"]),
        auth_service=auth_service,
    )

    assert response["success"] is True
    assert response["data"]["parentAccessToken"]


@pytest.mark.asyncio
async def test_invalid_refresh_fails(auth_service: AuthService) -> None:
    with pytest.raises(UnauthorizedException):
        await refresh_parent_token(
            RefreshTokenRequest(refreshToken="bad-refresh"),
            auth_service=auth_service,
        )


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token(auth_service: AuthService) -> None:
    login_data = await run_kakao_login(auth_service)

    logout_response = await logout(
        LogoutRequest(refreshToken=login_data["refreshToken"]),
        auth_service=auth_service,
    )
    assert logout_response == {
        "success": True,
        "data": {"message": "로그아웃되었습니다."},
    }

    with pytest.raises(UnauthorizedException):
        await refresh_parent_token(
            RefreshTokenRequest(refreshToken=login_data["refreshToken"]),
            auth_service=auth_service,
        )
