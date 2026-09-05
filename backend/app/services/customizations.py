from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models import ChildProfile, ProfileCustomization

DEFAULT_THEME_ID = "cream-book-room"

THEME_PRICES = {
    "cream-book-room": 0,
    "sky-dream-room": 250,
    "forest-cozy-room": 250,
    "sunset-lounge": 250,
    "night-star-room": 250,
    "ocean-blue-room": 250,
    "rainbow-room": 250,
    "mint-garden-room": 250,
    "winter-snow-room": 250,
    "space-adventure-room": 250,
}

POPO_ITEMS = {
    "sun-cap": ("hat", 80),
    "star-cap": ("hat", 120),
    "round-glasses": ("glasses", 90),
    "cool-glasses": ("glasses", 130),
    "star-necklace": ("necklace", 90),
    "heart-necklace": ("necklace", 110),
    "blue-hoodie": ("outfit", 150),
    "orange-vest": ("outfit", 150),
}

AVATAR_COST = 50


class CustomizationService:
    def __init__(self, *, session: AsyncSession) -> None:
        self.session = session

    async def get(self, *, profile: ChildProfile) -> dict:
        customization = await self._get_or_create(profile)
        await self.session.commit()
        return self._data(profile, customization)

    async def select_theme(self, *, profile: ChildProfile, theme_id: str) -> dict:
        if theme_id not in THEME_PRICES:
            raise AppException(status_code=400, detail="Unknown room theme.")
        customization = await self._get_or_create(profile)
        unlocked = self._string_list(customization.unlocked_theme_ids)
        if theme_id not in unlocked:
            self._spend(profile, customization, THEME_PRICES[theme_id])
            unlocked.append(theme_id)
            customization.unlocked_theme_ids = unlocked
        customization.selected_theme_id = theme_id
        await self.session.commit()
        return self._data(profile, customization)

    async def save_popo(self, *, profile: ChildProfile, selected_popo: dict[str, str | None]) -> dict:
        customization = await self._get_or_create(profile)
        normalized: dict[str, str] = {}
        for kind, item_id in selected_popo.items():
            if not item_id:
                continue
            item = POPO_ITEMS.get(item_id)
            if item is None or item[0] != kind:
                raise AppException(status_code=400, detail="Unknown Popo item.")
            normalized[kind] = item_id

        unlocked = self._string_list(customization.unlocked_popo_item_ids)
        new_items = [item_id for item_id in normalized.values() if item_id not in unlocked]
        cost = sum(POPO_ITEMS[item_id][1] for item_id in new_items)
        if cost:
            self._spend(profile, customization, cost)
            unlocked.extend(new_items)
            customization.unlocked_popo_item_ids = list(dict.fromkeys(unlocked))
        customization.selected_popo = normalized
        await self.session.commit()
        return self._data(profile, customization)

    async def save_avatar(
        self,
        *,
        profile: ChildProfile,
        avatar_index: int | None,
        profile_image_url: str | None,
        profile_color: str | None = None,
    ) -> dict:
        customization = await self._get_or_create(profile)
        unlocked = self._int_list(customization.unlocked_avatar_indices)

        if avatar_index is not None:
            if avatar_index not in unlocked:
                self._spend(profile, customization, AVATAR_COST)
                unlocked.append(avatar_index)
                customization.unlocked_avatar_indices = sorted(set(unlocked))
            profile.profile_image_id = avatar_index + 1

        profile.profile_image_url = profile_image_url
        if profile_color is not None:
            customization.profile_color = profile_color
        await self.session.commit()
        return self._data(profile, customization)

    async def _get_or_create(self, profile: ChildProfile) -> ProfileCustomization:
        result = await self.session.execute(
            select(ProfileCustomization).where(ProfileCustomization.profile_id == profile.profile_id)
        )
        customization = result.scalar_one_or_none()
        if customization is not None:
            return customization

        current_avatar_index = max((profile.profile_image_id or 1) - 1, 0)
        customization = ProfileCustomization(
            profile_id=profile.profile_id,
            selected_theme_id=DEFAULT_THEME_ID,
            unlocked_theme_ids=[DEFAULT_THEME_ID],
            selected_popo={},
            unlocked_popo_item_ids=[],
            unlocked_avatar_indices=[0, current_avatar_index],
            spent_stars=0,
        )
        self.session.add(customization)
        await self.session.flush()
        return customization

    @staticmethod
    def _data(profile: ChildProfile, customization: ProfileCustomization) -> dict:
        spent = max(0, customization.spent_stars or 0)
        total = max(0, profile.hearts or 0)
        return {
            "totalStars": total,
            "spentStars": spent,
            "availableStars": max(0, total - spent),
            "selectedThemeId": customization.selected_theme_id or DEFAULT_THEME_ID,
            "unlockedThemeIds": CustomizationService._string_list(customization.unlocked_theme_ids),
            "selectedPopo": customization.selected_popo or {},
            "unlockedPopoItemIds": CustomizationService._string_list(customization.unlocked_popo_item_ids),
            "unlockedAvatarIndices": CustomizationService._int_list(customization.unlocked_avatar_indices),
            "profileImageUrl": profile.profile_image_url,
            "profileImageId": profile.profile_image_id,
            "profileColor": customization.profile_color,
        }

    @staticmethod
    def _string_list(value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, str)]

    @staticmethod
    def _int_list(value: object) -> list[int]:
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, int)]

    @staticmethod
    def _spend(profile: ChildProfile, customization: ProfileCustomization, amount: int) -> None:
        available = max(0, (profile.hearts or 0) - (customization.spent_stars or 0))
        if amount > available:
            raise AppException(status_code=400, detail="Not enough stars.")
        customization.spent_stars = (customization.spent_stars or 0) + amount
