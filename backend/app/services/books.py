from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models import Book, ChildProfile, CourseType, Difficulty, LearningSession, LearningSessionStatus, UserBookProgress
from app.services.energy import EnergyService


class BookService:
    def __init__(self, *, session: AsyncSession) -> None:
        self.session = session
        self.energy_service = EnergyService()

    async def home(self, *, profile: ChildProfile) -> dict:
        energy = self.energy_service.apply_recharge(profile)
        attendance_dates = await self._attendance_dates(profile.profile_id)
        progress = await self._current_progress(profile.profile_id)
        current_book = None
        if progress is not None:
            book = await self._book_by_id(progress.book_id)
            if book is not None:
                current_book = self.current_book_data(book, progress)

        await self.session.commit()
        return {
            "profile": {
                "profileId": profile.profile_id,
                "nickname": profile.nickname,
                "difficulty": profile.difficulty.value if profile.difficulty else None,
            },
            "status": {
                "streakDays": profile.streak_days,
                "hearts": profile.hearts,
                "attendanceDates": attendance_dates,
                **energy,
            },
            "currentBook": current_book,
        }

    async def list_books(self, *, profile: ChildProfile) -> dict:
        books = await self._books_for_profile(profile)
        progress_by_book_id = await self._progress_by_book_id(profile.profile_id)
        return {
            "books": [
                self.book_list_item(
                    book,
                    progress_by_book_id.get(book.book_id),
                    total_lessons=await self._chapter_count(book.book_id),
                    default_unlocked=index == 0,
                )
                for index, book in enumerate(books)
            ]
        }

    async def book_detail(self, *, profile: ChildProfile, book_id: int) -> dict:
        book = await self._book_by_id(book_id)
        if book is None:
            raise AppException(status_code=404, detail="책을 찾을 수 없습니다.")
        progress = await self._progress_for_book(profile.profile_id, book_id)
        data = self.book_list_item(book, progress, total_lessons=await self._chapter_count(book.book_id))
        data["lessonName"] = book.lesson_name
        data["courses"] = self.course_items(progress.progress if progress else 0)
        return data

    async def _all_books(self) -> list[Book]:
        result = await self.session.execute(select(Book).order_by(Book.display_order, Book.book_id))
        return list(result.scalars().all())

    async def _attendance_dates(self, profile_id: int) -> list[str]:
        dates = (
            await self.session.execute(
                select(func.date(LearningSession.completed_at))
                .where(
                    LearningSession.profile_id == profile_id,
                    LearningSession.status == LearningSessionStatus.COMPLETED,
                    LearningSession.completed_at.is_not(None),
                )
                .group_by(func.date(LearningSession.completed_at))
                .order_by(func.date(LearningSession.completed_at).desc())
                .limit(30)
            )
        ).scalars().all()
        return [str(day) for day in dates]

    async def _books_for_profile(self, profile: ChildProfile) -> list[Book]:
        difficulty = profile.difficulty or Difficulty.BEGINNER
        result = await self.session.execute(
            select(Book)
            .where(Book.difficulty == difficulty)
            .order_by(Book.display_order, Book.book_id)
        )
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

    async def _chapter_count(self, book_id: int) -> int:
        from app.models import ReadingChunk

        result = await self.session.execute(
            select(func.count(func.distinct(ReadingChunk.chapter_number))).where(
                ReadingChunk.book_id == book_id
            )
        )
        return int(result.scalar_one() or 1)

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
            "coverColor": book.cover_color,
            "lessonName": book.lesson_name,
            "progress": progress.progress,
            "canResume": True,
        }

    @staticmethod
    def book_list_item(
        book: Book,
        progress: UserBookProgress | None,
        *,
        total_lessons: int = 1,
        default_unlocked: bool = False,
    ) -> dict:
        is_default_unlocked = progress is None and default_unlocked
        return {
            "bookId": book.book_id,
            "title": book.title,
            "coverImageUrl": book.cover_image_url,
            "coverColor": book.cover_color,
            "difficulty": book.difficulty.value if book.difficulty else None,
            "totalLessons": total_lessons,
            "currentLesson": max(1, round(((0 if progress is None else progress.progress) / 100) * total_lessons)),
            "locked": False if is_default_unlocked else True if progress is None else not progress.unlocked,
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
