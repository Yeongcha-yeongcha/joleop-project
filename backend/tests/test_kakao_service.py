import logging

import httpx

from app.core.config import Settings
from app.services import kakao as kakao_module
from app.services.kakao import KakaoService


def test_empty_kakao_client_secret_is_loaded_as_empty_string() -> None:
    settings = Settings(KAKAO_CLIENT_SECRET="")

    assert settings.KAKAO_CLIENT_SECRET == ""


def test_token_request_omits_empty_client_secret(monkeypatch) -> None:
    monkeypatch.setattr(kakao_module.settings, "KAKAO_CLIENT_ID", "rest-api-key")
    monkeypatch.setattr(kakao_module.settings, "KAKAO_CLIENT_SECRET", "")

    data = KakaoService()._build_token_request_data(
        authorization_code="authorization-code",
        redirect_uri="http://localhost:5173/oauth/kakao/callback",
    )

    assert data == {
        "grant_type": "authorization_code",
        "client_id": "rest-api-key",
        "redirect_uri": "http://localhost:5173/oauth/kakao/callback",
        "code": "authorization-code",
    }
    assert "client_secret" not in data


def test_token_request_includes_configured_client_secret(monkeypatch) -> None:
    monkeypatch.setattr(kakao_module.settings, "KAKAO_CLIENT_ID", "rest-api-key")
    monkeypatch.setattr(kakao_module.settings, "KAKAO_CLIENT_SECRET", "client-secret")

    data = KakaoService()._build_token_request_data(
        authorization_code="authorization-code",
        redirect_uri="http://localhost:5173/oauth/kakao/callback",
    )

    assert data["client_secret"] == "client-secret"


def test_kakao_error_log_excludes_credentials(caplog) -> None:
    response = httpx.Response(
        status_code=401,
        json={
            "error": "invalid_client",
            "error_description": "Bad client credentials",
        },
    )

    with caplog.at_level(logging.WARNING):
        KakaoService()._log_kakao_error(stage="token exchange", response=response)

    assert "status=401" in caplog.text
    assert "error=invalid_client" in caplog.text
    assert "description=Bad client credentials" in caplog.text
    assert "rest-api-key" not in caplog.text
    assert "client-secret" not in caplog.text
    assert "authorization-code" not in caplog.text
