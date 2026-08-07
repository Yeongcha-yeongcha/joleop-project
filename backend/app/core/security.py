from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from jwt import ExpiredSignatureError, InvalidTokenError

from app.core.config import settings
from app.models.enums import AuthTokenType


class TokenError(ValueError):
    pass


class ExpiredTokenError(TokenError):
    pass


password_hasher = PasswordHasher()


def _jwt_secret() -> str:
    if not settings.JWT_SECRET_KEY:
        raise TokenError("JWT_SECRET_KEY is not configured.")
    return settings.JWT_SECRET_KEY


def create_token(
    *,
    parent_id: int,
    token_type: AuthTokenType,
    expires_delta: timedelta,
    profile_id: int | None = None,
) -> str:
    expires_at = datetime.now(UTC) + expires_delta
    subject = profile_id if token_type == AuthTokenType.PROFILE else parent_id
    payload: dict[str, Any] = {
        "sub": str(subject),
        "tokenType": token_type.value,
        "parentId": parent_id,
        "exp": expires_at,
        "iat": datetime.now(UTC),
    }
    if profile_id is not None:
        payload["profileId"] = profile_id
    return jwt.encode(payload, _jwt_secret(), algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, _jwt_secret(), algorithms=[settings.JWT_ALGORITHM])
    except ExpiredSignatureError as exc:
        raise ExpiredTokenError("Expired token.") from exc
    except InvalidTokenError as exc:
        raise TokenError("Invalid token.") from exc


def create_parent_access_token(parent_id: int) -> str:
    return create_token(
        parent_id=parent_id,
        token_type=AuthTokenType.PARENT,
        expires_delta=timedelta(minutes=settings.PARENT_ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(parent_id: int) -> str:
    return create_token(
        parent_id=parent_id,
        token_type=AuthTokenType.REFRESH,
        expires_delta=timedelta(days=settings.PARENT_REFRESH_TOKEN_EXPIRE_DAYS),
    )


def create_profile_access_token(*, parent_id: int, profile_id: int) -> str:
    return create_token(
        parent_id=parent_id,
        profile_id=profile_id,
        token_type=AuthTokenType.PROFILE,
        expires_delta=timedelta(minutes=settings.PROFILE_ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def hash_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError):
        return False
