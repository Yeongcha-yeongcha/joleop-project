import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from sqlalchemy import delete, func, select
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


def load_json(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        if "accepted" in data:
            data = [item["lesson"] for item in data["accepted"]]
        elif "lessons" in data:
            data = data["lessons"]
        else:
            data = [data]
    return data


def lesson_number(item: dict[str, Any], fallback: int) -> int:
    return int(item.get("lesson_number") or item.get("episode") or fallback)


def page_items(lesson: dict[str, Any]) -> list[tuple[int, str]]:
    pages = []
    for index, page in enumerate(lesson.get("lesson") or lesson.get("pages") or [], start=1):
        if isinstance(page, str):
            pages.append((index, page))
            continue
        key = next((name for name in page if name.startswith("page")), None)
        if key is None:
            continue
        page_number = int(key.replace("page", "") or index)
        pages.append((page_number, str(page[key])))
    return pages


def question_type(value: str | None) -> DescriptionQuestionType:
    normalized = (value or "").lower()
    if normalized in {"word_guess", "word-guess", "wordguess"}:
        return DescriptionQuestionType.WORD_GUESS
    if normalized in {"why", "why_question", "why-question"}:
        return DescriptionQuestionType.WHY_QUESTION
    if normalized in {"description", "describe"}:
        return DescriptionQuestionType.DESCRIPTION
    return DescriptionQuestionType.FILL_BLANK


async def next_display_order(session: AsyncSession) -> int:
    result = await session.execute(select(func.max(Book.display_order)))
    return int(result.scalar_one_or_none() or 0) + 1


async def book_for_import(
    session: AsyncSession,
    *,
    book_id: int | None,
    title: str,
    difficulty: Difficulty,
    display_order: int | None = None,
    cover_image_url: str | None = None,
    cover_color: str | None = None,
) -> Book:
    if book_id is not None:
        result = await session.execute(select(Book).where(Book.book_id == book_id))
        book = result.scalar_one_or_none()
        if book is not None:
            book.title = title if title is not None else book.title
            book.difficulty = difficulty
            if display_order is not None:
                book.display_order = display_order
            if cover_image_url is not None:
                book.cover_image_url = cover_image_url
            if cover_color is not None:
                book.cover_color = cover_color
            return book

    result = await session.execute(
        select(Book).where(Book.title == title, Book.difficulty == difficulty)
    )
    book = result.scalar_one_or_none()
    if book is not None:
        book.lesson_name = book.lesson_name or "Lesson 1"
        if display_order is not None:
            book.display_order = display_order
        if cover_image_url is not None:
            book.cover_image_url = cover_image_url
        if cover_color is not None:
            book.cover_color = cover_color
        return book

    book = Book(
        title=title,
        lesson_name="Lesson 1",
        difficulty=difficulty,
        cover_image_url=cover_image_url,
        cover_color=cover_color,
        display_order=display_order if display_order is not None else await next_display_order(session),
    )
    session.add(book)
    await session.flush()
    return book


async def replace_book_content(
    session: AsyncSession,
    *,
    book: Book,
    accepted_lessons: list[dict[str, Any]],
    description_lessons: list[dict[str, Any]],
    roleplay_lessons: list[dict[str, Any]],
) -> dict[str, int]:
    await session.execute(delete(RoleplayMission).where(RoleplayMission.book_id == book.book_id))
    await session.execute(delete(DescriptionQuestion).where(DescriptionQuestion.book_id == book.book_id))
    await session.execute(delete(RepeatQuestion).where(RepeatQuestion.book_id == book.book_id))
    await session.execute(delete(ReadingChunk).where(ReadingChunk.book_id == book.book_id))

    description_by_lesson = {
        lesson_number(item, index): item
        for index, item in enumerate(description_lessons, start=1)
    }
    roleplay_by_lesson = {
        lesson_number(item, index): item
        for index, item in enumerate(roleplay_lessons, start=1)
    }

    reading_count = repeat_count = description_count = roleplay_count = 0

    for fallback, lesson in enumerate(accepted_lessons, start=1):
        current_lesson = lesson_number(lesson, fallback)
        if fallback == 1:
            book.lesson_name = f"Lesson {current_lesson}"
        reading_step = repeat_step = description_step = 1
        for page_number, text in page_items(lesson):
            session.add(
                ReadingChunk(
                    book_id=book.book_id,
                    chapter_number=current_lesson,
                    step=reading_step,
                    text=text,
                    image_url=None,
                )
            )
            reading_count += 1
            reading_step += 1

            session.add(
                RepeatQuestion(
                    book_id=book.book_id,
                    chapter_number=current_lesson,
                    step=repeat_step,
                    target_text=text,
                    image_url=None,
                )
            )
            repeat_count += 1
            repeat_step += 1

        description_item = description_by_lesson.get(current_lesson)
        for scene in (description_item or {}).get("description_scenes", []):
            session.add(
                DescriptionQuestion(
                    book_id=book.book_id,
                    chapter_number=current_lesson,
                    step=description_step,
                    question_type=question_type(scene.get("desc_type")),
                    instruction=scene.get("guide_hint") or "Look at the picture and answer.",
                    sentence=scene.get("sentence"),
                    image_url=scene.get("image_path") or None,
                    page_number=scene.get("page_number"),
                    source_text=scene.get("text"),
                    blank_word=scene.get("blank_word"),
                    answer_sentence=scene.get("answer_sentence"),
                    guide_hint=scene.get("guide_hint"),
                )
            )
            description_count += 1
            description_step += 1

        roleplay_item = roleplay_by_lesson.get(current_lesson)
        for index, scenario in enumerate((roleplay_item or {}).get("roleplay_scenarios", []), start=1):
            session.add(
                RoleplayMission(
                    book_id=book.book_id,
                    chapter_number=current_lesson,
                    title=scenario.get("topic") or f"Roleplay {current_lesson}-{index}",
                    description=scenario.get("scene_description") or lesson.get("theme") or "",
                    character_name=scenario.get("character_name") or "Friend",
                    character_image_url=scenario.get("character_image_url"),
                    opening_message=scenario.get("opening_message") or "Hi! Can you help me?",
                    player_goal=scenario.get("player_goal"),
                    model_answer=scenario.get("model_answer"),
                    similar_answers=scenario.get("similar_answers") or [],
                    hint_sequence=scenario.get("hint_sequence") or [],
                    required_turns=1,
                )
            )
            roleplay_count += 1

    return {
        "book_id": book.book_id,
        "reading_chunks": reading_count,
        "repeat_questions": repeat_count,
        "description_questions": description_count,
        "roleplay_missions": roleplay_count,
    }


async def import_content(args: argparse.Namespace) -> dict[str, int]:
    accepted_lessons = load_json(Path(args.accepted_text))
    description_lessons = load_json(Path(args.description_file) if args.description_file else None)
    roleplay_lessons = load_json(Path(args.roleplay_file) if args.roleplay_file else None)
    async with AsyncSessionLocal() as session:
        book = await book_for_import(
            session,
            book_id=args.book_id,
            title=args.title if args.title is not None else (accepted_lessons[0].get("story_title") if accepted_lessons else None) or "AI Story",
            difficulty=Difficulty(args.difficulty),
            display_order=args.display_order,
            cover_image_url=args.cover_image_url,
            cover_color=args.cover_color,
        )
        result = await replace_book_content(
            session,
            book=book,
            accepted_lessons=accepted_lessons,
            description_lessons=description_lessons,
            roleplay_lessons=roleplay_lessons,
        )
        await session.commit()
        return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import AI-generated story content into the app DB.")
    parser.add_argument("accepted_text", help="Path to *_accepted_text.json or batch output JSON.")
    parser.add_argument("--description-file", help="Path to generated description quiz JSON.")
    parser.add_argument("--roleplay-file", help="Path to generated roleplay quiz JSON.")
    parser.add_argument("--book-id", type=int, help="Existing book id to replace content for.")
    parser.add_argument("--title", help="Book title to create or update.")
    parser.add_argument("--display-order", type=int, help="Book display order.")
    parser.add_argument("--cover-image-url", help="Cover image URL/path for the imported book.")
    parser.add_argument("--cover-color", help="Cover color hex value for the imported book.")
    parser.add_argument(
        "--difficulty",
        choices=[item.value for item in Difficulty],
        default=Difficulty.BEGINNER.value,
    )
    return parser.parse_args()


async def main() -> None:
    result = await import_content(parse_args())
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
