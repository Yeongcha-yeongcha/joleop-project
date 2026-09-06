from functools import lru_cache
from pathlib import Path

from pydantic import Field, PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
WORKSPACE_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(WORKSPACE_DIR / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    PROJECT_NAME: str = "Children English Story Learning API"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: PostgresDsn = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/story_learning"
    )

    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"

    PARENT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    PARENT_REFRESH_TOKEN_EXPIRE_DAYS: int = 14
    PROFILE_ACCESS_TOKEN_EXPIRE_MINUTES: int = 180
    MAX_CHILD_PROFILES_PER_PARENT: int = 5
    PROFILE_IMAGE_BASE_URL: str = "https://cdn.example.com/profiles"
    MAX_AUDIO_UPLOAD_BYTES: int = 10 * 1024 * 1024
    COMPLETION_REWARD_HEARTS: int = 10
    COMPLETION_REWARD_ENERGY: int = 1
    ENERGY_RECHARGE_MINUTES: int = 15
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3:8b"

    TTS_PROVIDER: str = "edge"
    EDGE_TTS_VOICE: str = "en-US-JennyNeural"
    EDGE_TTS_CACHE_DIR: str = str(BACKEND_DIR / ".tts_cache")

    KAKAO_CLIENT_ID: str = ""
    KAKAO_CLIENT_SECRET: str = ""
    KAKAO_REDIRECT_URI: str = ""
    KAKAO_TOKEN_URL: str = "https://kauth.kakao.com/oauth/token"
    KAKAO_USER_INFO_URL: str = "https://kapi.kakao.com/v2/user/me"

    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost:5174"

    @computed_field
    @property
    def database_url(self) -> str:
        return str(self.DATABASE_URL)

    @computed_field
    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
