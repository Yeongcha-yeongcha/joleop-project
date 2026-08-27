from datetime import UTC, datetime

import pytest

from app.api.v1.learning_sessions import (
    get_learning_session,
    get_reading,
    start_or_resume_learning_session,
    update_reading_progress,
)
from app.core.exceptions import AppException, ForbiddenException
from app.models import (
    Book,
    ChildProfile,
    CourseType,
    Difficulty,
    LearningSession,
    LearningSessionStatus,
    ReadingChunk,
    UserBookProgress,
)
from app.schemas.learning import ReadingProgressRequest
from app.services.learning_sessions import LearningSessionService


class FakeScalarResult:
    def __init__(self, values):
        self.values = values

    def all(self):
        return self.values

    def first(self):
        return self.values[0] if self.values else None


class FakeResult:
    def __init__(self, value=None, values=None):
        self.value = value
        self.values = values

    def scalar_one_or_none(self):
        return self.value

    def scalars(self):
        return FakeScalarResult(self.values or [])


class FakeLearningSessionStore:
    def __init__(self) -> None:
        self.profile = ChildProfile(
            profile_id=101,
            parent_id=10,
            nickname="은정",
            age=8,
            password_hash="hash",
        )
        self.other_profile = ChildProfile(
            profile_id=102,
            parent_id=10,
            nickname="민준",
            age=9,
            password_hash="hash",
        )
        self.books = [
            Book(
                book_id=1,
                title="The Dragon Story",
                lesson_name="Lesson 1",
                difficulty=Difficulty.BEGINNER,
            )
        ]
        self.reading_chunks = [
            ReadingChunk(
                chunk_id=100 + step,
                book_id=1,
                step=step,
                text=f"Reading chunk {step}",
                image_url=f"https://cdn.example.com/books/1/{step}.png",
            )
            for step in range(1, 6)
        ]
        self.learning_sessions: list[LearningSession] = []
        self.user_book_progress: list[UserBookProgress] = []
        self.next_session_id = 128
        self.next_progress_id = 1

    async def execute(self, statement):
        entity = statement.column_descriptions[0].get("entity")
        params = statement.compile().params
        if entity is Book:
            return FakeResult(self._book(params["book_id_1"]))
        if entity is LearningSession:
            if "session_id_1" in params:
                return FakeResult(self._session(params["session_id_1"]))
            return FakeResult(
                values=self._active_sessions(
                    profile_id=params["profile_id_1"],
                    book_id=params["book_id_1"],
                )
            )
        if entity is ReadingChunk:
            return FakeResult(
                values=[
                    chunk
                    for chunk in self.reading_chunks
                    if chunk.book_id == params["book_id_1"]
                ]
            )
        if entity is UserBookProgress:
            return FakeResult(
                self._progress(
                    profile_id=params["profile_id_1"],
                    book_id=params["book_id_1"],
                )
            )
        raise AssertionError(f"Unexpected query: {statement}")

    def add(self, instance) -> None:
        if isinstance(instance, LearningSession):
            if instance.session_id is None:
                instance.session_id = self.next_session_id
                self.next_session_id += 1
            self.learning_sessions.append(instance)
            return
        if isinstance(instance, UserBookProgress):
            if instance.progress_id is None:
                instance.progress_id = self.next_progress_id
                self.next_progress_id += 1
            self.user_book_progress.append(instance)
            return
        raise AssertionError(f"Unexpected add: {instance}")

    async def flush(self) -> None:
        return None

    async def commit(self) -> None:
        return None

    async def refresh(self, instance) -> None:
        return None

    def _book(self, book_id: int) -> Book | None:
        return next((book for book in self.books if book.book_id == book_id), None)

    def _session(self, session_id: int) -> LearningSession | None:
        return next(
            (
                learning_session
                for learning_session in self.learning_sessions
                if learning_session.session_id == session_id
            ),
            None,
        )

    def _active_sessions(self, *, profile_id: int, book_id: int) -> list[LearningSession]:
        return sorted(
            [
                learning_session
                for learning_session in self.learning_sessions
                if learning_session.profile_id == profile_id
                and learning_session.book_id == book_id
                and learning_session.status
                in [
                    LearningSessionStatus.IN_PROGRESS,
                    LearningSessionStatus.EXITED,
                ]
            ],
            key=lambda learning_session: learning_session.session_id,
            reverse=True,
        )

    def _progress(
        self,
        *,
        profile_id: int,
        book_id: int,
    ) -> UserBookProgress | None:
        return next(
            (
                progress
                for progress in self.user_book_progress
                if progress.profile_id == profile_id and progress.book_id == book_id
            ),
            None,
        )

    def add_exited_session(self) -> LearningSession:
        learning_session = LearningSession(
            session_id=128,
            profile_id=101,
            book_id=1,
            status=LearningSessionStatus.EXITED,
            current_course=CourseType.READING,
            current_course_number=1,
            current_step=3,
            total_progress=10,
            started_at=datetime.now(UTC),
            last_studied_at=datetime.now(UTC),
        )
        self.learning_sessions.append(learning_session)
        self.next_session_id = 129
        return learning_session


@pytest.fixture
def learning_session_context():
    store = FakeLearningSessionStore()
    return {
        "store": store,
        "profile": store.profile,
        "other_profile": store.other_profile,
        "service": LearningSessionService(session=store),
    }


@pytest.mark.asyncio
async def test_new_session(learning_session_context) -> None:
    response = await start_or_resume_learning_session(
        1,
        current_profile=learning_session_context["profile"],
        learning_session_service=learning_session_context["service"],
    )

    assert response["data"] == {
        "sessionId": 128,
        "bookId": 1,
        "isNew": True,
        "status": "IN_PROGRESS",
        "currentCourse": "READING",
        "currentCourseNumber": 1,
        "currentStep": 1,
        "totalProgress": 0,
    }


@pytest.mark.asyncio
async def test_existing_session_resume(learning_session_context) -> None:
    learning_session_context["store"].add_exited_session()

    response = await start_or_resume_learning_session(
        1,
        current_profile=learning_session_context["profile"],
        learning_session_service=learning_session_context["service"],
    )

    assert response["data"]["isNew"] is False
    assert response["data"]["status"] == "IN_PROGRESS"
    assert response["data"]["currentStep"] == 3
    assert response["data"]["totalProgress"] == 10


@pytest.mark.asyncio
async def test_duplicate_session_is_not_created(learning_session_context) -> None:
    first = await start_or_resume_learning_session(
        1,
        current_profile=learning_session_context["profile"],
        learning_session_service=learning_session_context["service"],
    )
    second = await start_or_resume_learning_session(
        1,
        current_profile=learning_session_context["profile"],
        learning_session_service=learning_session_context["service"],
    )

    assert first["data"]["sessionId"] == second["data"]["sessionId"]
    assert len(learning_session_context["store"].learning_sessions) == 1


@pytest.mark.asyncio
async def test_session_ownership(learning_session_context) -> None:
    await start_or_resume_learning_session(
        1,
        current_profile=learning_session_context["profile"],
        learning_session_service=learning_session_context["service"],
    )

    with pytest.raises(ForbiddenException):
        await get_learning_session(
            128,
            current_profile=learning_session_context["other_profile"],
            learning_session_service=learning_session_context["service"],
        )


@pytest.mark.asyncio
async def test_reading_lookup(learning_session_context) -> None:
    await start_or_resume_learning_session(
        1,
        current_profile=learning_session_context["profile"],
        learning_session_service=learning_session_context["service"],
    )

    response = await get_reading(
        128,
        current_profile=learning_session_context["profile"],
        learning_session_service=learning_session_context["service"],
    )

    assert response["data"]["courseType"] == "READING"
    assert response["data"]["currentStep"] == 1
    assert response["data"]["totalSteps"] == 5
    assert response["data"]["courseProgress"] == 20
    assert response["data"]["content"]["chunkId"] == 101


@pytest.mark.asyncio
async def test_reading_progress(learning_session_context) -> None:
    await start_or_resume_learning_session(
        1,
        current_profile=learning_session_context["profile"],
        learning_session_service=learning_session_context["service"],
    )

    response = await update_reading_progress(
        128,
        ReadingProgressRequest(currentStep=1),
        current_profile=learning_session_context["profile"],
        learning_session_service=learning_session_context["service"],
    )

    assert response["data"]["currentStep"] == 2
    assert response["data"]["courseProgress"] == 40
    assert response["data"]["totalProgress"] == 10
    assert response["data"]["courseCompleted"] is False
    assert response["data"]["content"]["chunkId"] == 102


@pytest.mark.asyncio
async def test_invalid_step(learning_session_context) -> None:
    await start_or_resume_learning_session(
        1,
        current_profile=learning_session_context["profile"],
        learning_session_service=learning_session_context["service"],
    )

    with pytest.raises(AppException):
        await update_reading_progress(
            128,
            ReadingProgressRequest(currentStep=2),
            current_profile=learning_session_context["profile"],
            learning_session_service=learning_session_context["service"],
        )


@pytest.mark.asyncio
async def test_double_click_is_blocked(learning_session_context) -> None:
    await start_or_resume_learning_session(
        1,
        current_profile=learning_session_context["profile"],
        learning_session_service=learning_session_context["service"],
    )
    await update_reading_progress(
        128,
        ReadingProgressRequest(currentStep=1),
        current_profile=learning_session_context["profile"],
        learning_session_service=learning_session_context["service"],
    )

    with pytest.raises(AppException):
        await update_reading_progress(
            128,
            ReadingProgressRequest(currentStep=1),
            current_profile=learning_session_context["profile"],
            learning_session_service=learning_session_context["service"],
        )
    assert learning_session_context["store"].learning_sessions[0].current_step == 2


@pytest.mark.asyncio
async def test_reading_complete_moves_to_repeat(learning_session_context) -> None:
    learning_session = LearningSession(
        session_id=128,
        profile_id=101,
        book_id=1,
        status=LearningSessionStatus.IN_PROGRESS,
        current_course=CourseType.READING,
        current_course_number=1,
        current_step=5,
        total_progress=20,
        started_at=datetime.now(UTC),
        last_studied_at=datetime.now(UTC),
    )
    learning_session_context["store"].learning_sessions.append(learning_session)
    learning_session_context["store"].user_book_progress.append(
        UserBookProgress(
            progress_id=1,
            profile_id=101,
            book_id=1,
            progress=20,
            completed=False,
            unlocked=True,
        )
    )

    response = await update_reading_progress(
        128,
        ReadingProgressRequest(currentStep=5),
        current_profile=learning_session_context["profile"],
        learning_session_service=learning_session_context["service"],
    )

    assert response["data"] == {
        "courseProgress": 100,
        "totalProgress": 25,
        "courseCompleted": True,
        "nextCourse": "REPEAT",
    }
    assert learning_session.current_course == CourseType.REPEAT
    assert learning_session.current_course_number == 2
    assert learning_session.current_step == 1
