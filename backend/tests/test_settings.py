from app.core.config import Settings


def test_database_url_uses_asyncpg_driver() -> None:
    settings = Settings()
    assert settings.database_url.startswith("postgresql+asyncpg://")


def test_cors_origins_are_parsed_from_env_string() -> None:
    settings = Settings(CORS_ORIGINS="http://localhost:3000,http://localhost:5173")
    assert settings.cors_origins_list == [
        "http://localhost:3000",
        "http://localhost:5173",
    ]
