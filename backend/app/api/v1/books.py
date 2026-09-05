from fastapi import APIRouter, Depends

from app.api.deps import get_book_service, get_current_profile
from app.models import ChildProfile
from app.schemas.common import success_response
from app.services.books import BookService

home_router = APIRouter(prefix="/home", tags=["Home"])
router = APIRouter(prefix="/books", tags=["Books"])


@home_router.get("")
async def get_home(
    current_profile: ChildProfile = Depends(get_current_profile),
    book_service: BookService = Depends(get_book_service),
) -> dict:
    return success_response(await book_service.home(profile=current_profile))


@router.get("")
async def list_books(
    current_profile: ChildProfile = Depends(get_current_profile),
    book_service: BookService = Depends(get_book_service),
) -> dict:
    return success_response(await book_service.list_books(profile=current_profile))


@router.get("/{bookId}")
async def get_book_detail(
    bookId: int,
    current_profile: ChildProfile = Depends(get_current_profile),
    book_service: BookService = Depends(get_book_service),
) -> dict:
    return success_response(
        await book_service.book_detail(profile=current_profile, book_id=bookId)
    )
