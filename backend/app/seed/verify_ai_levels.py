import asyncio

from sqlalchemy import func, select

from app.db.session import AsyncSessionLocal
from app.models import Book, DescriptionQuestion, ReadingChunk, RepeatQuestion, RoleplayMission


async def main() -> None:
    async with AsyncSessionLocal() as session:
        books = (
            await session.execute(select(Book).order_by(Book.difficulty, Book.display_order, Book.book_id))
        ).scalars().all()
        for book in books:
            chapter_rows = await session.execute(
                select(
                    ReadingChunk.chapter_number,
                    func.count(func.distinct(ReadingChunk.chunk_id)),
                    func.count(func.distinct(RepeatQuestion.question_id)),
                    func.count(func.distinct(DescriptionQuestion.question_id)),
                    func.count(func.distinct(RoleplayMission.mission_id)),
                )
                .select_from(ReadingChunk)
                .outerjoin(
                    RepeatQuestion,
                    (RepeatQuestion.book_id == ReadingChunk.book_id)
                    & (RepeatQuestion.chapter_number == ReadingChunk.chapter_number),
                )
                .outerjoin(
                    DescriptionQuestion,
                    (DescriptionQuestion.book_id == ReadingChunk.book_id)
                    & (DescriptionQuestion.chapter_number == ReadingChunk.chapter_number),
                )
                .outerjoin(
                    RoleplayMission,
                    (RoleplayMission.book_id == ReadingChunk.book_id)
                    & (RoleplayMission.chapter_number == ReadingChunk.chapter_number),
                )
                .where(ReadingChunk.book_id == book.book_id)
                .group_by(ReadingChunk.chapter_number)
                .order_by(ReadingChunk.chapter_number)
            )
            print(f"book_id={book.book_id} level={book.difficulty.value} title={book.title!r}")
            for chapter, reading, repeat, description, roleplay in chapter_rows:
                print(
                    f"  chapter={chapter} reading={reading} repeat={repeat} "
                    f"description={description} roleplay={roleplay}"
                )


if __name__ == "__main__":
    asyncio.run(main())
