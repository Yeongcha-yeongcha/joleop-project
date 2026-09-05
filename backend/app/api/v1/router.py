from fastapi import APIRouter
from fastapi import status
from fastapi.responses import JSONResponse

from app.api.v1 import auth, books, customizations, learning_sessions, onboarding, parents, profiles, reviews, users
from app.db.session import database_is_ready

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(parents.router)
api_router.include_router(profiles.router)
api_router.include_router(profiles.profile_auth_router)
api_router.include_router(users.router)
api_router.include_router(onboarding.router)
api_router.include_router(books.home_router)
api_router.include_router(books.router)
api_router.include_router(learning_sessions.book_sessions_router)
api_router.include_router(learning_sessions.router)
api_router.include_router(reviews.router)
api_router.include_router(customizations.router)


@api_router.get("/health", tags=["health"])
async def api_health_check() -> dict[str, str]:
    return {"status": "ok"}


@api_router.get("/ready", tags=["health"])
async def api_readiness_check() -> JSONResponse:
    if await database_is_ready():
        return JSONResponse({"status": "ok", "database": "ok"})
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "unavailable", "database": "unavailable"},
    )
