from pydantic import BaseModel, Field


class KakaoLoginRequest(BaseModel):
    authorization_code: str = Field(alias="authorizationCode")
    redirect_uri: str | None = Field(default=None, alias="redirectUri")


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
