import pytest
from fastapi.routing import APIRoute

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
    assert "/api/v1/health" in paths


@pytest.mark.asyncio
async def test_health_check() -> None:
    response = await _route_endpoint("/health")()
    assert response == {"status": "ok"}


@pytest.mark.asyncio
async def test_api_v1_health_check() -> None:
    response = await _route_endpoint("/api/v1/health")()
    assert response == {"status": "ok"}
