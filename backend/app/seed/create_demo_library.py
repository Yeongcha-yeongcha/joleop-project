import asyncio
from dataclasses import dataclass

from sqlalchemy import delete, select

from app.db.session import AsyncSessionLocal
from app.models import (
    Book,
    ChildProfile,
    DescriptionQuestion,
    Difficulty,
    LearningAttempt,
    LearningSession,
    ReadingChunk,
    RepeatQuestion,
    ReviewAttempt,
    ReviewCard,
    RoleplayMessage,
    RoleplayMission,
    UserBookProgress,
)


@dataclass(frozen=True)
class DemoBook:
    title: str
    color: str
    cover_image_url: str


BOOK_SELECT_IMAGES = [
    "/images/BookSelect1.png",
    "/images/BookSelect2.png",
    "/images/BookSelect3.png",
    "/images/BookSelect4.png",
    "/images/BookSelect5.png",
    "/images/BookSelect6.png",
]


def demo_book(title: str, color: str, index: int) -> DemoBook:
    return DemoBook(title, color, BOOK_SELECT_IMAGES[index % len(BOOK_SELECT_IMAGES)])


DEMO_LIBRARY: dict[Difficulty, list[DemoBook]] = {
    Difficulty.BEGINNER: [
        demo_book("Sunny Meadow Friends", "#F7C948", 0),
        demo_book("Popo's Little Picnic", "#FF9F68", 1),
        demo_book("The Tiny Bird Bell", "#7ED6A7", 2),
        demo_book("Cloud Hat Day", "#82C7FF", 3),
        demo_book("The Red Balloon Path", "#FF7A85", 4),
        demo_book("Momo's Cozy Tunnel", "#B892FF", 5),
        demo_book("Toto Finds a Star", "#FFD166", 6),
        demo_book("Pipi's Rainbow Song", "#6EE7D8", 7),
        demo_book("The Sleepy Sunflower", "#F28AB2", 8),
        demo_book("Popo's Thank You Day", "#A3D977", 9),
    ],
    Difficulty.INTERMEDIATE: [
        demo_book("Forest Bridge Quest", "#5FB67A", 1),
        demo_book("The Moonlit Treehouse", "#6F9CEB", 2),
        demo_book("Popo and the Wind Map", "#F4A261", 3),
        demo_book("The Hidden Acorn Door", "#9BDE7E", 4),
        demo_book("Cloud Castle Rescue", "#8ECAE6", 5),
        demo_book("The Lantern Parade", "#E76F51", 6),
        demo_book("Momo's River Plan", "#B088F9", 7),
        demo_book("Pipi's Message Race", "#2EC4B6", 8),
        demo_book("The Silver Kite", "#ADB5BD", 9),
        demo_book("Friends at Blue Hill", "#4D96FF", 10),
    ],
    Difficulty.ADVANCED: [
        demo_book("The Secret Star Atlas", "#6F83D8", 2),
        demo_book("Popo's Clocktower Promise", "#845EC2", 3),
        demo_book("The Midnight Library", "#2F3A8F", 4),
        demo_book("Bridge Beyond the Clouds", "#577590", 5),
        demo_book("The Crystal Compass", "#43AA8B", 6),
        demo_book("Momo and the Echo Cave", "#BC6C25", 7),
        demo_book("Pipi's Sky Signal", "#3A86FF", 8),
        demo_book("The Golden Key Debate", "#E9C46A", 9),
        demo_book("Toto's Clever Machine", "#00A6A6", 10),
        demo_book("The Last Lantern Trail", "#D8577B", 11),
    ],
}


async def _source_book(session, difficulty: Difficulty, target_titles: set[str]) -> Book:
    source = (
        await session.execute(
            select(Book)
            .where(Book.difficulty == difficulty, ~Book.title.in_(target_titles))
            .order_by(Book.display_order, Book.book_id)
        )
    ).scalars().first()
    if source is not None:
        return source

    source = (
        await session.execute(
            select(Book)
            .where(Book.difficulty == difficulty)
            .order_by(Book.display_order, Book.book_id)
        )
    ).scalars().first()
    if source is None:
        raise RuntimeError(f"No source book found for {difficulty.value}.")
    return source


async def _content_snapshot(session, source: Book) -> dict:
    return {
        "reading": list((
            await session.execute(
                select(ReadingChunk)
                .where(ReadingChunk.book_id == source.book_id)
                .order_by(ReadingChunk.chapter_number, ReadingChunk.step)
            )
        ).scalars().all()),
        "repeat": list((
            await session.execute(
                select(RepeatQuestion)
                .where(RepeatQuestion.book_id == source.book_id)
                .order_by(RepeatQuestion.chapter_number, RepeatQuestion.step)
            )
        ).scalars().all()),
        "description": list((
            await session.execute(
                select(DescriptionQuestion)
                .where(DescriptionQuestion.book_id == source.book_id)
                .order_by(DescriptionQuestion.chapter_number, DescriptionQuestion.step)
            )
        ).scalars().all()),
        "roleplay": list((
            await session.execute(
                select(RoleplayMission)
                .where(RoleplayMission.book_id == source.book_id)
                .order_by(RoleplayMission.chapter_number, RoleplayMission.mission_id)
            )
        ).scalars().all()),
    }


async def _book_for_demo(
    session,
    *,
    difficulty: Difficulty,
    item: DemoBook,
    display_order: int,
) -> Book:
    book = (
        await session.execute(
            select(Book).where(Book.difficulty == difficulty, Book.title == item.title)
        )
    ).scalar_one_or_none()
    if book is None:
        book = Book(
            title=item.title,
            lesson_name="Lesson 1",
            difficulty=difficulty,
            cover_image_url=item.cover_image_url,
            cover_color=item.color,
            display_order=display_order,
        )
        session.add(book)
        await session.flush()
        return book

    book.lesson_name = "Lesson 1"
    book.cover_image_url = item.cover_image_url
    book.cover_color = item.color
    book.display_order = display_order
    return book


async def _replace_content(session, book: Book, snapshot: dict) -> dict[str, int]:
    for model in [DescriptionQuestion, RepeatQuestion, ReadingChunk, RoleplayMission]:
        await session.execute(delete(model).where(model.book_id == book.book_id))

    counts = {
        "reading_chunks": 0,
        "repeat_questions": 0,
        "description_questions": 0,
        "roleplay_missions": 0,
    }
    for chunk in snapshot["reading"]:
        session.add(
            ReadingChunk(
                book_id=book.book_id,
                chapter_number=chunk.chapter_number,
                step=chunk.step,
                text=chunk.text,
                image_url=chunk.image_url,
            )
        )
        counts["reading_chunks"] += 1

    for question in snapshot["repeat"]:
        session.add(
            RepeatQuestion(
                book_id=book.book_id,
                chapter_number=question.chapter_number,
                step=question.step,
                target_text=question.target_text,
                image_url=question.image_url,
            )
        )
        counts["repeat_questions"] += 1

    for question in snapshot["description"]:
        session.add(
            DescriptionQuestion(
                book_id=book.book_id,
                chapter_number=question.chapter_number,
                step=question.step,
                question_type=question.question_type,
                instruction=question.instruction,
                sentence=question.sentence,
                image_url=question.image_url,
                page_number=question.page_number,
                source_text=question.source_text,
                blank_word=question.blank_word,
                answer_sentence=question.answer_sentence,
                guide_hint=question.guide_hint,
            )
        )
        counts["description_questions"] += 1

    for mission in snapshot["roleplay"]:
        session.add(
            RoleplayMission(
                book_id=book.book_id,
                chapter_number=mission.chapter_number,
                title=mission.title,
                description=mission.description,
                character_name=mission.character_name,
                character_image_url=mission.character_image_url,
                opening_message=mission.opening_message,
                player_goal=mission.player_goal,
                model_answer=mission.model_answer,
                similar_answers=mission.similar_answers,
                hint_sequence=mission.hint_sequence,
                required_turns=mission.required_turns,
            )
        )
        counts["roleplay_missions"] += 1
    return counts


async def _sync_progress(session, books_by_difficulty: dict[Difficulty, list[Book]]) -> int:
    profiles = list((
        await session.execute(select(ChildProfile).where(ChildProfile.deleted_at.is_(None)))
    ).scalars().all())
    changed = 0
    for profile in profiles:
        difficulty = profile.difficulty or Difficulty.BEGINNER
        books = books_by_difficulty.get(difficulty, [])
        for index, book in enumerate(books):
            progress = (
                await session.execute(
                    select(UserBookProgress).where(
                        UserBookProgress.profile_id == profile.profile_id,
                        UserBookProgress.book_id == book.book_id,
                    )
                )
            ).scalar_one_or_none()
            unlocked = index < 3
            if progress is None:
                session.add(
                    UserBookProgress(
                        profile_id=profile.profile_id,
                        book_id=book.book_id,
                        progress=0,
                        completed=False,
                        unlocked=unlocked,
                    )
                )
                changed += 1
                continue
            if progress.unlocked != unlocked:
                progress.unlocked = unlocked
                changed += 1
    return changed


async def _delete_extra_books(session, keep_titles: set[str]) -> int:
    extras = list((
        await session.execute(select(Book).where(~Book.title.in_(keep_titles)))
    ).scalars().all())
    book_ids = [book.book_id for book in extras]
    if not book_ids:
        return 0

    session_ids = list((
        await session.execute(
            select(LearningSession.session_id).where(LearningSession.book_id.in_(book_ids))
        )
    ).scalars().all())
    mission_ids = list((
        await session.execute(
            select(RoleplayMission.mission_id).where(RoleplayMission.book_id.in_(book_ids))
        )
    ).scalars().all())
    review_card_ids = list((
        await session.execute(select(ReviewCard.card_id).where(ReviewCard.book_id.in_(book_ids)))
    ).scalars().all())

    if session_ids:
        await session.execute(delete(LearningAttempt).where(LearningAttempt.session_id.in_(session_ids)))
        await session.execute(delete(RoleplayMessage).where(RoleplayMessage.session_id.in_(session_ids)))
        await session.execute(delete(LearningSession).where(LearningSession.session_id.in_(session_ids)))
    if mission_ids:
        await session.execute(delete(RoleplayMessage).where(RoleplayMessage.mission_id.in_(mission_ids)))
    if review_card_ids:
        await session.execute(delete(ReviewAttempt).where(ReviewAttempt.card_id.in_(review_card_ids)))
        await session.execute(delete(ReviewCard).where(ReviewCard.card_id.in_(review_card_ids)))

    for model in [
        DescriptionQuestion,
        RepeatQuestion,
        ReadingChunk,
        RoleplayMission,
        UserBookProgress,
        Book,
    ]:
        await session.execute(delete(model).where(model.book_id.in_(book_ids)))
    return len(book_ids)


async def create_demo_library() -> dict[str, int]:
    async with AsyncSessionLocal() as session:
        target_titles = {item.title for items in DEMO_LIBRARY.values() for item in items}
        result = {
            "books": 0,
            "reading_chunks": 0,
            "repeat_questions": 0,
            "description_questions": 0,
            "roleplay_missions": 0,
            "user_book_progress": 0,
            "extra_books_deleted": 0,
        }
        books_by_difficulty: dict[Difficulty, list[Book]] = {}

        for difficulty, items in DEMO_LIBRARY.items():
            source = await _source_book(session, difficulty, target_titles)
            snapshot = await _content_snapshot(session, source)
            books_by_difficulty[difficulty] = []
            for index, item in enumerate(items, start=1):
                book = await _book_for_demo(
                    session,
                    difficulty=difficulty,
                    item=item,
                    display_order=index,
                )
                books_by_difficulty[difficulty].append(book)
                result["books"] += 1
                counts = await _replace_content(session, book, snapshot)
                for key, count in counts.items():
                    result[key] += count

        result["user_book_progress"] = await _sync_progress(session, books_by_difficulty)
        result["extra_books_deleted"] = await _delete_extra_books(session, target_titles)
        await session.commit()
        return result


async def main() -> None:
    result = await create_demo_library()
    print("Demo library created:")
    for name, count in result.items():
        print(f"- {name}: {count}")


if __name__ == "__main__":
    asyncio.run(main())
