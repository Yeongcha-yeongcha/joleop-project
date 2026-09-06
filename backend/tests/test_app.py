import json

import pytest
from fastapi.routing import APIRoute

from app.api.v1 import router as api_router_module
from app import main as main_module
from app.main import app


def test_app_imports() -> None:
    assert app.title


def _route_endpoint(path: str):
    for route in app.routes:
        if isinstance(route, APIRoute) and route.path == path:
            return route.endpoint
    raise AssertionError(f"Route not found: {path}")


def test_health_routes_are_registered() -> None:
    paths = [route.path for route in app.routes if isinstance(route, APIRoute)]
    assert "/health" in paths
    assert "/ready" in paths
    assert "/api/v1/health" in paths
    assert "/api/v1/ready" in paths


@pytest.mark.asyncio
async def test_health_check() -> None:
    response = await _route_endpoint("/health")()
    assert response == {"status": "ok"}


@pytest.mark.asyncio
async def test_api_v1_health_check() -> None:
    response = await _route_endpoint("/api/v1/health")()
    assert response == {"status": "ok"}


@pytest.mark.asyncio
async def test_readiness_check_success(monkeypatch: pytest.MonkeyPatch) -> None:
    async def ready() -> bool:
        return True

    monkeypatch.setattr(main_module, "database_is_ready", ready)

    response = await _route_endpoint("/ready")()

    assert response.status_code == 200
    assert json.loads(response.body) == {"status": "ok", "database": "ok"}


@pytest.mark.asyncio
async def test_api_v1_readiness_check_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    async def not_ready() -> bool:
        return False

    monkeypatch.setattr(api_router_module, "database_is_ready", not_ready)

    response = await _route_endpoint("/api/v1/ready")()

    assert response.status_code == 503
    assert json.loads(response.body) == {
        "status": "unavailable",
        "database": "unavailable",
    }
