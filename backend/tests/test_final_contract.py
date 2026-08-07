import json
from datetime import UTC, datetime

import pytest
from fastapi.exceptions import RequestValidationError

from app.api.v1.learning_sessions import (
    complete_learning_session,
    create_roleplay_message,
    exit_learning_session,
    get_learning_session_result,
    get_roleplay,
)
from app.core.exceptions import SessionAlreadyCompletedException, validation_exception_handler
from app.main import app
from app.models import (
    ChildProfile,
    CourseType,
    LearningSession,
    LearningSessionStatus,
    RoleplayMessage,
    RoleplayMission,
    UserBookProgress,
)
from app.services.learning_sessions import LearningSessionService
from app.services.speech import MockSpeechToTextService


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


class FakeUploadFile:
    content_type = "audio/wav"

    async def read(self) -> bytes:
        return b"Hello dragon"


class FakeRoleplayStore:
    def __init__(self) -> None:
        self.profile = ChildProfile(
            profile_id=101,
            parent_id=10,
            nickname="은정",
            age=8,
            password_hash="hash",
        )
        self.learning_session = LearningSession(
            session_id=128,
            profile_id=101,
            book_id=1,
            status=LearningSessionStatus.IN_PROGRESS,
            current_course=CourseType.ROLEPLAY,
            current_course_number=4,
            current_step=1,
            total_progress=75,
            total_score=None,
            stars=None,
            started_at=datetime.now(UTC),
            last_studied_at=datetime.now(UTC),
        )
        self.progress = UserBookProgress(
            progress_id=1,
            profile_id=101,
            book_id=1,
            progress=75,
            completed=False,
            unlocked=True,
        )
        self.mission = RoleplayMission(
            mission_id=401,
            book_id=1,
            title="Help the Dragon",
            description="Talk with the dragon.",
            character_name="Dori",
            character_image_url="https://cdn.example.com/dori.png",
            opening_message="Can you help me?",
            required_turns=1,
        )
        self.messages: list[RoleplayMessage] = []
        self.next_message_id = 1

    async def execute(self, statement):
        entity = statement.column_descriptions[0].get("entity")
        params = statement.compile().params
        if entity is LearningSession:
            return FakeResult(
                self.learning_session
                if self.learning_session.session_id == params["session_id_1"]
                else None
            )
        if entity is RoleplayMission:
            return FakeResult(values=[self.mission])
        if entity is RoleplayMessage:
            return FakeResult(
                values=[
                    message
                    for message in self.messages
                    if message.session_id == params["session_id_1"]
                ]
            )
        if entity is UserBookProgress:
            return FakeResult(self.progress)
        raise AssertionError(f"Unexpected query: {statement}")

    def add(self, instance) -> None:
        if isinstance(instance, RoleplayMessage):
            instance.message_id = self.next_message_id
            self.next_message_id += 1
            instance.created_at = datetime.now(UTC)
            self.messages.append(instance)
            return
        raise AssertionError(f"Unexpected add: {instance}")

    async def flush(self) -> None:
        return None

    async def commit(self) -> None:
        return None

    async def refresh(self, instance) -> None:
        return None


@pytest.fixture
def roleplay_context():
    store = FakeRoleplayStore()
    return {
        "store": store,
        "profile": store.profile,
        "service": LearningSessionService(session=store),
        "speech": MockSpeechToTextService(),
    }


def test_required_endpoints_exist() -> None:
    actual = {
        (next(iter(route.methods - {"HEAD", "OPTIONS"})), route.path)
        for route in app.routes
        if hasattr(route, "methods")
    }
    expected = {
        ("POST", "/api/v1/auth/kakao"),
        ("POST", "/api/v1/auth/logout"),
        ("POST", "/api/v1/auth/refresh"),
        ("GET", "/api/v1/parents/me"),
        ("GET", "/api/v1/profiles"),
        ("POST", "/api/v1/profiles"),
        ("PATCH", "/api/v1/profiles/{profileId}"),
        ("DELETE", "/api/v1/profiles/{profileId}"),
        ("PATCH", "/api/v1/profiles/{profileId}/password"),
        ("POST", "/api/v1/profiles/{profileId}/login"),
        ("POST", "/api/v1/profile-auth/logout"),
        ("GET", "/api/v1/profiles/me"),
        ("POST", "/api/v1/profiles/me/onboarding"),
        ("GET", "/api/v1/home"),
        ("GET", "/api/v1/books"),
        ("GET", "/api/v1/books/{bookId}"),
        ("POST", "/api/v1/books/{bookId}/sessions"),
        ("GET", "/api/v1/learning-sessions/{sessionId}"),
        ("GET", "/api/v1/learning-sessions/{sessionId}/reading"),
        ("PATCH", "/api/v1/learning-sessions/{sessionId}/reading/progress"),
        ("GET", "/api/v1/learning-sessions/{sessionId}/repeat"),
        ("POST", "/api/v1/learning-sessions/{sessionId}/repeat/attempts"),
        ("PATCH", "/api/v1/learning-sessions/{sessionId}/repeat/progress"),
        ("GET", "/api/v1/learning-sessions/{sessionId}/description"),
        ("POST", "/api/v1/learning-sessions/{sessionId}/description/attempts"),
        ("PATCH", "/api/v1/learning-sessions/{sessionId}/description/progress"),
        ("GET", "/api/v1/learning-sessions/{sessionId}/roleplay"),
        ("POST", "/api/v1/learning-sessions/{sessionId}/roleplay/messages"),
        ("POST", "/api/v1/learning-sessions/{sessionId}/exit"),
        ("POST", "/api/v1/learning-sessions/{sessionId}/complete"),
        ("GET", "/api/v1/learning-sessions/{sessionId}/result"),
    }
    assert expected.issubset(actual)


@pytest.mark.asyncio
async def test_validation_error_uses_common_response() -> None:
    response = await validation_exception_handler(None, RequestValidationError([]))
    assert response.status_code == 422
    assert json.loads(response.body) == {
        "success": False,
        "error": {
            "code": "INVALID_REQUEST",
            "message": "요청 값이 올바르지 않습니다.",
        },
    }


@pytest.mark.asyncio
async def test_roleplay(roleplay_context) -> None:
    response = await get_roleplay(
        128,
        current_profile=roleplay_context["profile"],
        learning_session_service=roleplay_context["service"],
    )
    assert response["data"]["mission"]["missionId"] == 401


@pytest.mark.asyncio
async def test_roleplay_audio(roleplay_context) -> None:
    response = await create_roleplay_message(
        128,
        audio=FakeUploadFile(),
        mission_id=401,
        current_profile=roleplay_context["profile"],
        learning_session_service=roleplay_context["service"],
        speech_to_text_service=roleplay_context["speech"],
    )
    assert response["data"]["userTranscript"] == "Hello dragon"
    assert response["data"]["missionCompleted"] is True


@pytest.mark.asyncio
async def test_exit_complete_result_and_recomplete_block(roleplay_context) -> None:
    exit_response = await exit_learning_session(
        128,
        current_profile=roleplay_context["profile"],
        learning_session_service=roleplay_context["service"],
    )
    assert exit_response["data"]["status"] == "EXITED"

    complete_response = await complete_learning_session(
        128,
        current_profile=roleplay_context["profile"],
        learning_session_service=roleplay_context["service"],
    )
    assert complete_response["data"]["status"] == "COMPLETED"

    result_response = await get_learning_session_result(
        128,
        current_profile=roleplay_context["profile"],
        learning_session_service=roleplay_context["service"],
    )
    assert result_response["data"]["totalProgress"] == 100

    with pytest.raises(SessionAlreadyCompletedException):
        await complete_learning_session(
            128,
            current_profile=roleplay_context["profile"],
            learning_session_service=roleplay_context["service"],
        )
