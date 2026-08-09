from fastapi import APIRouter

from app.api.v1 import auth, books, learning_sessions, onboarding, parents, profiles

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(parents.router)
api_router.include_router(profiles.router)
api_router.include_router(profiles.profile_auth_router)
api_router.include_router(onboarding.router)
api_router.include_router(books.home_router)
api_router.include_router(books.router)
api_router.include_router(learning_sessions.book_sessions_router)
api_router.include_router(learning_sessions.router)


@api_router.get("/health", tags=["health"])
async def api_health_check() -> dict[str, str]:
    return {"status": "ok"}
