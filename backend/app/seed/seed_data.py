import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models import (
    Book,
    DescriptionQuestion,
    DescriptionQuestionType,
    Difficulty,
    ReadingChunk,
    RepeatQuestion,
    RoleplayMission,
)

DEFAULT_BOOKS = [
    {
        "title": "The Dragon Story",
        "lesson_name": "Lesson 1",
        "difficulty": Difficulty.BEGINNER,
        "cover_image_url": "/images/BookSample_A.png",
        "display_order": 1,
    },
    {
        "title": "Fresh Lemonade!",
        "lesson_name": "Lesson 1",
        "difficulty": Difficulty.BEGINNER,
        "cover_image_url": "/images/BookSample_B.png",
        "display_order": 2,
    },
    {
        "title": "The Snack Museum",
        "lesson_name": "Lesson 1",
        "difficulty": Difficulty.BEGINNER,
        "cover_image_url": "/images/BookSample_C.png",
        "display_order": 3,
    },
    {
        "title": "Magic Forest",
        "lesson_name": "Lesson 1",
        "difficulty": Difficulty.INTERMEDIATE,
        "cover_image_url": "/images/onboarding/bg-tree-house.png",
        "display_order": 4,
    },
    {
        "title": "Cloud Castle",
        "lesson_name": "Lesson 1",
        "difficulty": Difficulty.INTERMEDIATE,
        "cover_image_url": "/images/onboarding/bg-castle-path.png",
        "display_order": 5,
    },
    {
        "title": "Sunny Picnic",
        "lesson_name": "Lesson 1",
        "difficulty": Difficulty.ADVANCED,
        "cover_image_url": "/images/onboarding/bg-meadow-house.png",
        "display_order": 6,
    },
]


async def ensure_default_books(session: AsyncSession) -> tuple[Book, int]:
    created = 0
    dragon_book: Book | None = None

    for item in DEFAULT_BOOKS:
        result = await session.execute(
            select(Book).where(
                Book.title == item["title"],
                Book.lesson_name == item["lesson_name"],
                Book.difficulty == item["difficulty"],
            )
        )
        book = result.scalar_one_or_none()
        if book is None:
            book = Book(**item)
            session.add(book)
            await session.flush()
            created += 1
        else:
            book.cover_image_url = item["cover_image_url"]
            book.display_order = item["display_order"]
            book.lesson_name = item["lesson_name"]

        if item["title"] == "The Dragon Story":
            dragon_book = book

    if dragon_book is None:
        raise RuntimeError("Default Dragon Story seed book was not created.")
    return dragon_book, created


async def get_or_create_book(session: AsyncSession) -> tuple[Book, bool]:
    result = await session.execute(
        select(Book).where(
            Book.title == "The Dragon Story",
            Book.lesson_name == "Lesson 1",
            Book.difficulty == Difficulty.BEGINNER,
        )
    )
    book = result.scalar_one_or_none()
    if book:
        return book, False

    book = Book(
        title="The Dragon Story",
        lesson_name="Lesson 1",
        difficulty=Difficulty.BEGINNER,
        cover_image_url="/images/BookSample_A.png",
        display_order=1,
    )
    session.add(book)
    await session.flush()
    return book, True


async def ensure_reading_chunks(session: AsyncSession, book: Book) -> int:
    chunks = [
        (1, "A little dragon lived in a warm cave.", "Dragon+Cave"),
        (2, "Every morning, the dragon looked at the bright sky.", "Bright+Sky"),
        (3, "He wanted to fly over the green forest.", "Green+Forest"),
        (4, "His friend Mia said, 'You can try today!'", "Mia+Friend"),
        (5, "The little dragon flapped his wings and smiled.", "Dragon+Flying"),
    ]
    created = 0
    for step, text, image_text in chunks:
        result = await session.execute(
            select(ReadingChunk).where(
                ReadingChunk.book_id == book.book_id,
                ReadingChunk.step == step,
            )
        )
        if result.scalar_one_or_none():
            continue
        session.add(
            ReadingChunk(
                book_id=book.book_id,
                step=step,
                text=text,
                image_url=f"https://placehold.co/600x400?text={image_text}",
            )
        )
        created += 1
    return created


async def ensure_repeat_questions(session: AsyncSession, book: Book) -> int:
    questions = [
        (1, "I am a little dragon.", "Repeat+Dragon"),
        (2, "I can fly today.", "Repeat+Fly"),
        (3, "My friend helps me.", "Repeat+Friend"),
    ]
    created = 0
    for step, target_text, image_text in questions:
        result = await session.execute(
            select(RepeatQuestion).where(
                RepeatQuestion.book_id == book.book_id,
                RepeatQuestion.step == step,
            )
        )
        if result.scalar_one_or_none():
            continue
        session.add(
            RepeatQuestion(
                book_id=book.book_id,
                step=step,
                target_text=target_text,
                image_url=f"https://placehold.co/600x400?text={image_text}",
            )
        )
        created += 1
    return created


async def ensure_description_questions(session: AsyncSession, book: Book) -> int:
    questions = [
        (
            1,
            DescriptionQuestionType.FILL_BLANK,
            "Fill in the blank.",
            "The little dragon lives in a ____ cave.",
            "Fill+Blank",
        ),
        (
            2,
            DescriptionQuestionType.DESCRIPTION,
            "Describe what you see in the picture.",
            None,
            "Describe+Picture",
        ),
        (
            3,
            DescriptionQuestionType.WHY_QUESTION,
            "Why does the dragon want to fly?",
            None,
            "Why+Question",
        ),
    ]
    created = 0
    for step, question_type, instruction, sentence, image_text in questions:
        result = await session.execute(
            select(DescriptionQuestion).where(
                DescriptionQuestion.book_id == book.book_id,
                DescriptionQuestion.step == step,
            )
        )
        if result.scalar_one_or_none():
            continue
        session.add(
            DescriptionQuestion(
                book_id=book.book_id,
                step=step,
                question_type=question_type,
                instruction=instruction,
                sentence=sentence,
                image_url=f"https://placehold.co/600x400?text={image_text}",
            )
        )
        created += 1
    return created


async def ensure_roleplay_missions(session: AsyncSession, book: Book) -> int:
    result = await session.execute(
        select(RoleplayMission).where(
            RoleplayMission.book_id == book.book_id,
            RoleplayMission.title == "Help the Little Dragon Fly",
        )
    )
    if result.scalar_one_or_none():
        return 0

    session.add(
        RoleplayMission(
            book_id=book.book_id,
            title="Help the Little Dragon Fly",
            description="Encourage the little dragon and help him try flying.",
            character_name="Dori",
            character_image_url="https://placehold.co/600x400?text=Dori+Dragon",
            opening_message="Hi! I am Dori. I want to fly today. Can you help me?",
            required_turns=3,
        )
    )
    return 1


async def seed() -> dict[str, int]:
    async with AsyncSessionLocal() as session:
        book, books_created = await ensure_default_books(session)
        result = {
            "books": books_created,
            "reading_chunks": await ensure_reading_chunks(session, book),
            "repeat_questions": await ensure_repeat_questions(session, book),
            "description_questions": await ensure_description_questions(session, book),
            "roleplay_missions": await ensure_roleplay_missions(session, book),
        }
        await session.commit()
        return result


async def main() -> None:
    result = await seed()
    print("Seed completed:")
    for name, count in result.items():
        print(f"- {name}: {count} created")


if __name__ == "__main__":
    asyncio.run(main())
