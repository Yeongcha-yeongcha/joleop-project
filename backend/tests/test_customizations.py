import pytest

from app.models import ChildProfile, ProfileCustomization
from app.services.customizations import CustomizationService


class FakeResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class FakeCustomizationSession:
    def __init__(self, customization: ProfileCustomization) -> None:
        self.customization = customization
        self.added = []

    async def execute(self, statement):
        return FakeResult(self.customization)

    def add(self, instance) -> None:
        self.added.append(instance)

    async def commit(self) -> None:
        return None


@pytest.fixture
def customization_context():
    profile = ChildProfile(
        profile_id=101,
        parent_id=10,
        nickname="Test",
        age=8,
        password_hash="hash",
        hearts=500,
    )
    customization = ProfileCustomization(
        customization_id=1,
        profile_id=101,
        selected_theme_id="cream-gradient",
        unlocked_theme_ids=["cream-gradient"],
        selected_popo={},
        unlocked_popo_item_ids=[],
        unlocked_avatar_indices=[0],
        spent_stars=0,
    )
    session = FakeCustomizationSession(customization)
    return profile, customization, CustomizationService(session=session)


@pytest.mark.asyncio
async def test_current_frontend_theme_can_be_bought_and_selected(customization_context) -> None:
    profile, customization, service = customization_context

    result = await service.select_theme(profile=profile, theme_id="pink-stripe")

    assert result["selectedThemeId"] == "pink-stripe"
    assert result["unlockedThemeIds"] == ["cream-gradient", "pink-stripe"]
    assert result["availableStars"] == 320
    assert customization.spent_stars == 180


@pytest.mark.asyncio
async def test_current_frontend_popo_items_can_be_bought_and_equipped(customization_context) -> None:
    profile, customization, service = customization_context

    result = await service.save_popo(
        profile=profile,
        selected_popo={
            "glasses": "heart-sunglass",
            "necklace": "rainbow-necklace",
        },
    )

    assert result["selectedPopo"] == {
        "glasses": "heart-sunglass",
        "necklace": "rainbow-necklace",
    }
    assert result["unlockedPopoItemIds"] == ["heart-sunglass", "rainbow-necklace"]
    assert result["availableStars"] == 320
    assert customization.spent_stars == 180
