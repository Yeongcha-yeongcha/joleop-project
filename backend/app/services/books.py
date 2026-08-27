from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models import Book, ChildProfile, CourseType, UserBookProgress


class BookService:
    def __init__(self, *, session: AsyncSession) -> None:
        self.session = session

    async def home(self, *, profile: ChildProfile) -> dict:
        progress = await self._current_progress(profile.profile_id)
        current_book = None
        if progress is not None:
            book = await self._book_by_id(progress.book_id)
            if book is not None:
                current_book = self.current_book_data(book, progress)

        return {
            "profile": {
                "profileId": profile.profile_id,
                "nickname": profile.nickname,
                "difficulty": profile.difficulty.value if profile.difficulty else None,
            },
            "status": {
                "streakDays": profile.streak_days,
                "hearts": profile.hearts,
                "energy": profile.energy,
                "maxEnergy": profile.max_energy,
            },
            "currentBook": current_book,
        }

    async def list_books(self, *, profile: ChildProfile) -> dict:
        books = await self._all_books()
        progress_by_book_id = await self._progress_by_book_id(profile.profile_id)
        return {
            "books": [
                self.book_list_item(book, progress_by_book_id.get(book.book_id))
                for book in books
            ]
        }

    async def book_detail(self, *, profile: ChildProfile, book_id: int) -> dict:
        book = await self._book_by_id(book_id)
        if book is None:
            raise AppException(status_code=404, detail="책을 찾을 수 없습니다.")
        progress = await self._progress_for_book(profile.profile_id, book_id)
        data = self.book_list_item(book, progress)
        data["lessonName"] = book.lesson_name
        data["courses"] = self.course_items(progress.progress if progress else 0)
        return data

    async def _all_books(self) -> list[Book]:
        result = await self.session.execute(select(Book).order_by(Book.display_order, Book.book_id))
        return list(result.scalars().all())

    async def _book_by_id(self, book_id: int) -> Book | None:
        result = await self.session.execute(select(Book).where(Book.book_id == book_id))
        return result.scalar_one_or_none()

    async def _progress_by_book_id(self, profile_id: int) -> dict[int, UserBookProgress]:
        result = await self.session.execute(
            select(UserBookProgress).where(UserBookProgress.profile_id == profile_id)
        )
        return {progress.book_id: progress for progress in result.scalars().all()}

    async def _progress_for_book(
        self,
        profile_id: int,
        book_id: int,
    ) -> UserBookProgress | None:
        result = await self.session.execute(
            select(UserBookProgress).where(
                UserBookProgress.profile_id == profile_id,
                UserBookProgress.book_id == book_id,
            )
        )
        return result.scalar_one_or_none()

    async def _current_progress(self, profile_id: int) -> UserBookProgress | None:
        progress_by_book_id = await self._progress_by_book_id(profile_id)
        candidates = [
            progress
            for progress in progress_by_book_id.values()
            if progress.unlocked and not progress.completed and progress.progress > 0
        ]
        if not candidates:
            return None
        return max(
            candidates,
            key=lambda progress: (
                progress.last_studied_at is not None,
                progress.last_studied_at,
                progress.progress_id,
            ),
        )

    @staticmethod
    def current_book_data(book: Book, progress: UserBookProgress) -> dict:
        return {
            "bookId": book.book_id,
            "title": book.title,
            "coverImageUrl": book.cover_image_url,
            "lessonName": book.lesson_name,
            "progress": progress.progress,
            "canResume": True,
        }

    @staticmethod
    def book_list_item(book: Book, progress: UserBookProgress | None) -> dict:
        return {
            "bookId": book.book_id,
            "title": book.title,
            "coverImageUrl": book.cover_image_url,
            "difficulty": book.difficulty.value if book.difficulty else None,
            "locked": True if progress is None else not progress.unlocked,
            "completed": False if progress is None else progress.completed,
            "progress": 0 if progress is None else progress.progress,
        }

    @staticmethod
    def course_items(progress: int) -> list[dict]:
        courses = [
            (1, CourseType.READING, "전체 동화 읽기"),
            (2, CourseType.REPEAT, "따라 말하기"),
            (3, CourseType.DESCRIPTION, "묘사"),
            (4, CourseType.ROLEPLAY, "롤플레잉"),
        ]
        return [
            {
                "courseNumber": course_number,
                "courseType": course_type.value,
                "title": title,
                "completed": progress >= course_number * 25,
            }
            for course_number, course_type, title in courses
        ]
