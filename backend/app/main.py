from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import http_exception_handler, validation_exception_handler
from app.db.session import database_is_ready

OPENAPI_TAGS = [
    {"name": "Auth", "description": "Kakao parent login, refresh, logout."},
    {"name": "Parents", "description": "Authenticated parent APIs."},
    {"name": "Profiles", "description": "Child profile management and profile auth."},
    {"name": "Onboarding", "description": "Child onboarding and difficulty placement."},
    {"name": "Home", "description": "Profile home dashboard."},
    {"name": "Books", "description": "Library and book detail APIs."},
    {"name": "Learning - Reading", "description": "Session start and reading course."},
    {"name": "Learning - Repeat", "description": "Repeat course and audio attempts."},
    {
        "name": "Learning - Description",
        "description": "Description course and audio attempts.",
    },
    {"name": "Learning - Roleplay", "description": "Mock roleplay course flow."},
    {"name": "Reviews", "description": "Spaced review cards and memory scheduling."},
    {"name": "Customization", "description": "Room, Popo, and avatar customization."},
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        lifespan=lifespan,
        openapi_tags=OPENAPI_TAGS,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_origin_regex=r"^http://(localhost|127\.0\.0\.1):\d+$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready", tags=["health"])
    async def readiness_check() -> JSONResponse:
        if await database_is_ready():
            return JSONResponse({"status": "ok", "database": "ok"})
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unavailable", "database": "unavailable"},
        )

    return app


app = create_app()
