from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import Difficulty


class ProfileCreateRequest(BaseModel):
    nickname: str = Field(min_length=1, max_length=30)
    age: int = Field(ge=3, le=13)
    profile_password: str = Field(alias="profilePassword", min_length=1, max_length=100)
    profile_image_id: int | None = Field(default=None, alias="profileImageId", ge=1)


class ProfileUpdateRequest(BaseModel):
    nickname: str | None = Field(default=None, min_length=1, max_length=30)
    age: int | None = Field(default=None, ge=3, le=13)
    profile_image_id: int | None = Field(default=None, alias="profileImageId", ge=1)


class ProfilePasswordUpdateRequest(BaseModel):
    new_password: str = Field(alias="newPassword", min_length=1, max_length=100)


class ProfileLoginRequest(BaseModel):
    profile_password: str = Field(alias="profilePassword", min_length=1, max_length=100)


class ProfileListItem(BaseModel):
    profile_id: int = Field(alias="profileId")
    nickname: str
    age: int
    profile_image_url: str | None = Field(alias="profileImageUrl")
    password_enabled: bool = Field(alias="passwordEnabled")
    onboarding_completed: bool = Field(alias="onboardingCompleted")
    difficulty: Difficulty | None

    model_config = {"populate_by_name": True}


class ProfileDetail(ProfileListItem):
    created_at: datetime | None = Field(default=None, alias="createdAt")


class ProfileLoginData(BaseModel):
    profile_access_token: str = Field(alias="profileAccessToken")
    profile: dict

    model_config = {"populate_by_name": True}
