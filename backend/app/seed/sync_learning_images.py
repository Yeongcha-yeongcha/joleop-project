import asyncio

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models import Book, DescriptionQuestion, ReadingChunk, RepeatQuestion
from app.seed.import_ai_content import page_image_url


async def sync_learning_images() -> dict[str, int]:
    counts = {"reading_chunks": 0, "repeat_questions": 0, "description_questions": 0}
    async with AsyncSessionLocal() as session:
        books = list((await session.execute(select(Book))).scalars().all())
        for book in books:
            reading_chunks = list((
                await session.execute(select(ReadingChunk).where(ReadingChunk.book_id == book.book_id))
            ).scalars().all())
            for chunk in reading_chunks:
                image_url = page_image_url(
                    difficulty=book.difficulty,
                    lesson_number=chunk.chapter_number,
                    page_number=chunk.step,
                )
                if image_url and chunk.image_url != image_url:
                    chunk.image_url = image_url
                    counts["reading_chunks"] += 1

            repeat_questions = list((
                await session.execute(select(RepeatQuestion).where(RepeatQuestion.book_id == book.book_id))
            ).scalars().all())
            for question in repeat_questions:
                image_url = page_image_url(
                    difficulty=book.difficulty,
                    lesson_number=question.chapter_number,
                    page_number=question.step,
                )
                if image_url and question.image_url != image_url:
                    question.image_url = image_url
                    counts["repeat_questions"] += 1

            description_questions = list((
                await session.execute(
                    select(DescriptionQuestion).where(DescriptionQuestion.book_id == book.book_id)
                )
            ).scalars().all())
            for question in description_questions:
                image_url = page_image_url(
                    difficulty=book.difficulty,
                    lesson_number=question.chapter_number,
                    page_number=question.page_number or question.step,
                )
                if image_url and question.image_url != image_url:
                    question.image_url = image_url
                    counts["description_questions"] += 1

        await session.commit()
    return counts


async def main() -> None:
    counts = await sync_learning_images()
    print("Learning images synchronized:")
    for name, count in counts.items():
        print(f"- {name}: {count}")


if __name__ == "__main__":
    asyncio.run(main())
