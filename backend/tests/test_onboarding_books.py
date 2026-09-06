from datetime import UTC, datetime

import pytest
from fastapi.security import HTTPAuthorizationCredentials

from app.api.deps import get_current_profile
from app.api.v1.books import get_book_detail, get_home, list_books
from app.api.v1.onboarding import submit_onboarding
from app.core.config import settings
from app.core.exceptions import OnboardingAlreadyCompletedException, UnauthorizedException
from app.core.security import create_parent_access_token, create_profile_access_token
from app.models import (
    Book,
    ChildProfile,
    Difficulty,
    OnboardingResult,
    UserBookProgress,
)
from app.schemas.onboarding import OnboardingSubmitRequest
from app.services.books import BookService
from app.services.onboarding import OnboardingService
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


class FakeLearningSession:
    def __init__(self) -> None:
        self.child_profiles = [
            ChildProfile(
                profile_id=101,
                parent_id=10,
                nickname="은정",
                age=8,
                password_hash="hash",
                difficulty=None,
                onboarding_completed=False,
                streak_days=15,
                hearts=210,
                energy=4,
                max_energy=5,
            ),
            ChildProfile(
                profile_id=202,
                parent_id=20,
                nickname="민준",
                age=9,
                password_hash="hash",
                difficulty=Difficulty.BEGINNER,
                onboarding_completed=True,
                streak_days=1,
                hearts=10,
                energy=5,
                max_energy=5,
            ),
        ]
        self.books = [
            Book(
                book_id=1,
                title="The Dragon Story",
                lesson_name="Lesson 1",
                difficulty=Difficulty.BEGINNER,
                cover_image_url="https://cdn.example.com/books/1/cover.png",
                display_order=1,
            ),
            Book(
                book_id=2,
                title="The Space Story",
                lesson_name="Lesson 2",
                difficulty=Difficulty.INTERMEDIATE,
                cover_image_url="https://cdn.example.com/books/2/cover.png",
                display_order=2,
            ),
        ]
        self.progress = [
            UserBookProgress(
                progress_id=1,
                profile_id=101,
                book_id=1,
                progress=25,
                completed=False,
                unlocked=True,
                last_studied_at=datetime.now(UTC),
            ),
            UserBookProgress(
                progress_id=2,
                profile_id=202,
                book_id=1,
                progress=75,
                completed=False,
                unlocked=True,
                last_studied_at=datetime.now(UTC),
            ),
            UserBookProgress(
                progress_id=3,
                profile_id=101,
                book_id=2,
                progress=0,
                completed=False,
                unlocked=False,
                last_studied_at=None,
            ),
        ]
        self.onboarding_results: list[OnboardingResult] = []

    async def execute(self, statement):
        entity = statement.column_descriptions[0].get("entity")
        params = statement.compile().params
        if entity is ChildProfile:
            return FakeResult(
                self._profile(
                    parent_id=params["parent_id_1"],
                    profile_id=params["profile_id_1"],
                )
            )
        if entity is Book:
            if "book_id_1" in params:
                return FakeResult(self._book(params["book_id_1"]))
            return FakeResult(values=sorted(self.books, key=lambda book: book.display_order))
        if entity is UserBookProgress:
            if "book_id_1" in params:
                return FakeResult(
                    self._progress(
                        profile_id=params["profile_id_1"],
                        book_id=params["book_id_1"],
                    )
                )
            return FakeResult(
                values=[
                    progress
                    for progress in self.progress
                    if progress.profile_id == params["profile_id_1"]
                ]
            )
        raise AssertionError(f"Unexpected query: {statement}")

    def add(self, instance) -> None:
        if isinstance(instance, OnboardingResult):
            instance.onboarding_result_id = len(self.onboarding_results) + 1
            self.onboarding_results.append(instance)
            return
        raise AssertionError(f"Unexpected add: {instance}")

    async def commit(self) -> None:
        return None

    async def refresh(self, instance) -> None:
        return None

    def _profile(self, *, parent_id: int, profile_id: int) -> ChildProfile | None:
        return next(
            (
                profile
                for profile in self.child_profiles
                if profile.parent_id == parent_id
                and profile.profile_id == profile_id
                and profile.deleted_at is None
            ),
            None,
        )

    def _book(self, book_id: int) -> Book | None:
        return next((book for book in self.books if book.book_id == book_id), None)

    def _progress(self, *, profile_id: int, book_id: int) -> UserBookProgress | None:
        return next(
            (
                progress
                for progress in self.progress
                if progress.profile_id == profile_id and progress.book_id == book_id
            ),
            None,
        )


@pytest.fixture
def learning_context():
    settings.JWT_SECRET_KEY = "test-secret-at-least-32-bytes-long"
    session = FakeLearningSession()
    return {
        "session": session,
        "profile": session.child_profiles[0],
        "other_profile": session.child_profiles[1],
        "profile_service": ProfileService(session=session),
        "onboarding_service": OnboardingService(session=session),
        "book_service": BookService(session=session),
    }


def onboarding_request() -> OnboardingSubmitRequest:
    return OnboardingSubmitRequest(
        answers=[
            {"questionId": 1, "answer": "A"},
            {"questionId": 2, "answer": "B"},
            {"questionId": 3, "answer": "A"},
        ]
    )


@pytest.mark.asyncio
async def test_onboarding(learning_context) -> None:
    response = await submit_onboarding(
        onboarding_request(),
        current_profile=learning_context["profile"],
        onboarding_service=learning_context["onboarding_service"],
    )

    assert response["data"] == {
        "profileId": 101,
        "onboardingScore": 6,
        "difficulty": "BEGINNER",
        "onboardingCompleted": True,
    }
    assert learning_context["profile"].difficulty == Difficulty.BEGINNER
    assert len(learning_context["session"].onboarding_results) == 1


@pytest.mark.asyncio
async def test_duplicate_onboarding_is_blocked(learning_context) -> None:
    await submit_onboarding(
        onboarding_request(),
        current_profile=learning_context["profile"],
        onboarding_service=learning_context["onboarding_service"],
    )

    with pytest.raises(OnboardingAlreadyCompletedException):
        await submit_onboarding(
            onboarding_request(),
            current_profile=learning_context["profile"],
            onboarding_service=learning_context["onboarding_service"],
        )


@pytest.mark.asyncio
async def test_home(learning_context) -> None:
    learning_context["profile"].difficulty = Difficulty.BEGINNER
    response = await get_home(
        current_profile=learning_context["profile"],
        book_service=learning_context["book_service"],
    )

    assert response["data"]["profile"] == {
        "profileId": 101,
        "nickname": "은정",
        "difficulty": "BEGINNER",
    }
    assert response["data"]["status"]["energy"] == 4
    assert response["data"]["currentBook"]["bookId"] == 1
    assert response["data"]["currentBook"]["progress"] == 25


@pytest.mark.asyncio
async def test_home_current_book_null(learning_context) -> None:
    learning_context["session"].progress = []

    response = await get_home(
        current_profile=learning_context["profile"],
        book_service=learning_context["book_service"],
    )

    assert response["data"]["currentBook"] is None


@pytest.mark.asyncio
async def test_book_list(learning_context) -> None:
    response = await list_books(
        current_profile=learning_context["profile"],
        book_service=learning_context["book_service"],
    )

    books = response["data"]["books"]
    assert books[0]["bookId"] == 1
    assert books[0]["locked"] is False
    assert books[0]["progress"] == 25
    assert books[1]["locked"] is True


@pytest.mark.asyncio
async def test_progress_is_separated_by_profile(learning_context) -> None:
    response = await list_books(
        current_profile=learning_context["other_profile"],
        book_service=learning_context["book_service"],
    )

    assert response["data"]["books"][0]["progress"] == 75


@pytest.mark.asyncio
async def test_book_detail(learning_context) -> None:
    response = await get_book_detail(
        1,
        current_profile=learning_context["profile"],
        book_service=learning_context["book_service"],
    )

    data = response["data"]
    assert data["bookId"] == 1
    assert data["locked"] is False
    assert data["courses"][0] == {
        "courseNumber": 1,
        "courseType": "READING",
        "title": "전체 동화 읽기",
        "completed": True,
    }
    assert data["courses"][1]["completed"] is False


@pytest.mark.asyncio
async def test_locked_book_detail(learning_context) -> None:
    response = await get_book_detail(
        2,
        current_profile=learning_context["profile"],
        book_service=learning_context["book_service"],
    )

    assert response["data"]["locked"] is True
    assert response["data"]["progress"] == 0


@pytest.mark.asyncio
async def test_parent_token_is_blocked_from_profile_apis(learning_context) -> None:
    parent_token = create_parent_access_token(10)
    with pytest.raises(UnauthorizedException):
        await get_current_profile(
            HTTPAuthorizationCredentials(scheme="Bearer", credentials=parent_token),
            profile_service=learning_context["profile_service"],
        )

    profile_token = create_profile_access_token(parent_id=10, profile_id=101)
    profile = await get_current_profile(
        HTTPAuthorizationCredentials(scheme="Bearer", credentials=profile_token),
        profile_service=learning_context["profile_service"],
    )
    assert profile.profile_id == 101
