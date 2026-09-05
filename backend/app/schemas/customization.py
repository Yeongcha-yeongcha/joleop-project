from pydantic import BaseModel, Field


class PopoSelection(BaseModel):
    hat: str | None = None
    glasses: str | None = None
    necklace: str | None = None
    outfit: str | None = None


class ThemeSelectRequest(BaseModel):
    theme_id: str = Field(alias="themeId", min_length=1, max_length=80)


class PopoSaveRequest(BaseModel):
    selected_popo: PopoSelection = Field(alias="selectedPopo")


class AvatarSaveRequest(BaseModel):
    avatar_index: int | None = Field(default=None, alias="avatarIndex", ge=0, le=20)
    profile_image_url: str | None = Field(default=None, alias="profileImageUrl")
    profile_color: str | None = Field(default=None, alias="profileColor", max_length=40)


class CustomizationData(BaseModel):
    total_stars: int = Field(alias="totalStars")
    spent_stars: int = Field(alias="spentStars")
    available_stars: int = Field(alias="availableStars")
    selected_theme_id: str = Field(alias="selectedThemeId")
    unlocked_theme_ids: list[str] = Field(alias="unlockedThemeIds")
    selected_popo: dict[str, str] = Field(alias="selectedPopo")
    unlocked_popo_item_ids: list[str] = Field(alias="unlockedPopoItemIds")
    unlocked_avatar_indices: list[int] = Field(alias="unlockedAvatarIndices")
    profile_image_url: str | None = Field(alias="profileImageUrl")
    profile_image_id: int | None = Field(alias="profileImageId")
    profile_color: str | None = Field(alias="profileColor")

    model_config = {"populate_by_name": True}
