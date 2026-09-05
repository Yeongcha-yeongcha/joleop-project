from pydantic import BaseModel, ConfigDict, Field


class KakaoLoginRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    authorization_code: str = Field(alias="authorizationCode")
    redirect_uri: str | None = Field(default=None, alias="redirectUri")


class ParentPasswordSignupRequest(BaseModel):
    username: str = Field(min_length=4, max_length=30, pattern=r"^[A-Za-z0-9_]+$")
    password: str = Field(min_length=6, max_length=100)
    nickname: str | None = Field(default=None, max_length=30)


class ParentPasswordLoginRequest(BaseModel):
    username: str = Field(min_length=4, max_length=30)
    password: str = Field(min_length=1, max_length=100)


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(alias="refreshToken")


class LogoutRequest(BaseModel):
    refresh_token: str = Field(alias="refreshToken")


class TokenPairData(BaseModel):
    parent_access_token: str = Field(alias="parentAccessToken")
    refresh_token: str = Field(alias="refreshToken")
    is_new_parent: bool = Field(alias="isNewParent")
    parent: dict

    model_config = {"populate_by_name": True}


class RefreshData(BaseModel):
    parent_access_token: str = Field(alias="parentAccessToken")

    model_config = {"populate_by_name": True}
