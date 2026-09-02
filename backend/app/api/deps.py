from collections.abc import AsyncGenerator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedException
from app.db.session import get_db_session
from app.models import ChildProfile, Parent
from app.services.auth import AuthService
from app.services.books import BookService
from app.services.learning_sessions import LearningSessionService
from app.services.onboarding import OnboardingService
from app.services.profiles import ProfileService
from app.services.reviews import ReviewService
from app.services.speech import MockSpeechToTextService, SpeechToTextService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db_session():
        yield session


bearer_scheme = HTTPBearer(auto_error=False)


def get_auth_service(session: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(session=session)


def get_profile_service(session: AsyncSession = Depends(get_db)) -> ProfileService:
    return ProfileService(session=session)


def get_onboarding_service(session: AsyncSession = Depends(get_db)) -> OnboardingService:
    return OnboardingService(session=session)


def get_book_service(session: AsyncSession = Depends(get_db)) -> BookService:
    return BookService(session=session)


def get_learning_session_service(
    session: AsyncSession = Depends(get_db),
) -> LearningSessionService:
    return LearningSessionService(session=session)


def get_review_service(session: AsyncSession = Depends(get_db)) -> ReviewService:
    return ReviewService(session=session)


def get_speech_to_text_service() -> SpeechToTextService:
    return MockSpeechToTextService()


async def get_current_parent(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> Parent:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedException("인증이 필요합니다.")
    return await auth_service.get_parent_by_access_token(credentials.credentials)


async def get_current_profile(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    profile_service: ProfileService = Depends(get_profile_service),
) -> ChildProfile:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedException("인증이 필요합니다.")
    return await profile_service.get_profile_by_access_token(credentials.credentials)
