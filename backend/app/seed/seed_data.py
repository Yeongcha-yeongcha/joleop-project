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
        "title": "Bad Morning",
        "lesson_name": "Lesson 1",
        "difficulty": Difficulty.BEGINNER,
        "cover_image_url": None,
        "display_order": 4,
    },
    {
        "title": "Little Star",
        "lesson_name": "Lesson 1",
        "difficulty": Difficulty.BEGINNER,
        "cover_image_url": None,
        "display_order": 5,
    },
    {
        "title": "Magic Forest",
        "lesson_name": "Lesson 1",
        "difficulty": Difficulty.INTERMEDIATE,
        "cover_image_url": None,
        "display_order": 7,
    },
    {
        "title": "Cloud Castle",
        "lesson_name": "Lesson 1",
        "difficulty": Difficulty.INTERMEDIATE,
        "cover_image_url": None,
        "display_order": 9,
    },
    {
        "title": "Sunny Day",
        "lesson_name": "Lesson 1",
        "difficulty": Difficulty.INTERMEDIATE,
        "cover_image_url": None,
        "display_order": 6,
    },
    {
        "title": "Ocean Friends",
        "lesson_name": "Lesson 1",
        "difficulty": Difficulty.INTERMEDIATE,
        "cover_image_url": None,
        "display_order": 8,
    },
    {
        "title": "Rainbow Bridge",
        "lesson_name": "Lesson 1",
        "difficulty": Difficulty.INTERMEDIATE,
        "cover_image_url": None,
        "display_order": 10,
    },
    {
        "title": "Tiny Robot",
        "lesson_name": "Lesson 1",
        "difficulty": Difficulty.ADVANCED,
        "cover_image_url": None,
        "display_order": 11,
    },
    {
        "title": "Jungle Race",
        "lesson_name": "Lesson 1",
        "difficulty": Difficulty.ADVANCED,
        "cover_image_url": None,
        "display_order": 12,
    },
    {
        "title": "Moon Cake",
        "lesson_name": "Lesson 1",
        "difficulty": Difficulty.ADVANCED,
        "cover_image_url": None,
        "display_order": 13,
    },
    {
        "title": "Deep Sea",
        "lesson_name": "Lesson 1",
        "difficulty": Difficulty.ADVANCED,
        "cover_image_url": None,
        "display_order": 14,
    },
    {
        "title": "Star Patrol",
        "lesson_name": "Lesson 1",
        "difficulty": Difficulty.ADVANCED,
        "cover_image_url": None,
        "display_order": 15,
    },
]

SAMPLE_COURSE_CONTENT = {
    "The Dragon Story": {
        "reading": [
            (1, "Dori is a little dragon with shiny yellow wings.", "Dori+Dragon"),
            (2, "He lives in a warm cave near the green forest.", "Warm+Cave"),
            (3, "Today, Dori wants to fly above the tall trees.", "Tall+Trees"),
            (4, "Mia says, 'Take a deep breath and flap your wings.'", "Mia+Helps"),
            (5, "Dori jumps, flaps, and flies over the sunny hill.", "Dori+Flying"),
        ],
        "repeat": [
            (1, "I am a little dragon.", "Repeat+Dragon"),
            (2, "I live in a warm cave.", "Repeat+Cave"),
            (3, "I can fly over the trees.", "Repeat+Fly"),
            (4, "My friend helps me try.", "Repeat+Friend"),
        ],
        "description": [
            (
                1,
                DescriptionQuestionType.WORD_GUESS,
                "Fill in the blank.",
                "Dori lives in a warm ____.",
                "Blank+Cave",
                "cave",
                "Dori lives in a warm cave.",
                "Look at Dori's home.",
            ),
            (
                2,
                DescriptionQuestionType.DESCRIPTION,
                "Describe what Dori is doing.",
                None,
                "Describe+Flying",
                None,
                "Dori is flying.",
                "Say what the dragon is doing.",
            ),
            (
                3,
                DescriptionQuestionType.WHY_QUESTION,
                "Why does Mia help Dori?",
                None,
                "Why+Mia",
                None,
                "Mia helps Dori because he wants to fly.",
                "Think about Dori's dream.",
            ),
        ],
        "roleplay": {
            "title": "Help Dori Fly",
            "description": "Encourage Dori and help him fly over the trees.",
            "character_name": "Dori",
            "character_image_url": "https://placehold.co/600x400?text=Dori+Dragon",
            "opening_message": "Hi! I want to fly today, but I feel a little scared.",
            "player_goal": "Encourage Dori and tell him what to do first.",
            "model_answer": "You can do it, Dori. Take a deep breath and flap your wings.",
            "similar_answers": [
                "You can do it.",
                "Take a deep breath.",
                "Flap your wings.",
                "I will help you fly.",
            ],
            "hint_sequence": [
                "Tell Dori he can do it.",
                "Say 'take a deep breath.'",
                "Tell Dori to flap his wings.",
            ],
            "required_turns": 3,
        },
    },
    "Fresh Lemonade!": {
        "reading": [
            (1, "Lina picks three lemons from a small tree.", "Lina+Lemons"),
            (2, "She squeezes the lemons into a big glass jar.", "Squeeze+Lemons"),
            (3, "Her brother adds cold water and two spoons of sugar.", "Cold+Water"),
            (4, "They stir the lemonade until it tastes sweet.", "Sweet+Lemonade"),
        ],
        "repeat": [
            (1, "I pick three lemons.", "Repeat+Lemons"),
            (2, "I add cold water.", "Repeat+Water"),
            (3, "The lemonade is sweet.", "Repeat+Sweet"),
        ],
        "description": [
            (
                1,
                DescriptionQuestionType.WORD_GUESS,
                "Fill in the blank.",
                "Lina picks three ____.",
                "Blank+Lemons",
                "lemons",
                "Lina picks three lemons.",
                "Look at the yellow fruit.",
            ),
            (
                2,
                DescriptionQuestionType.DESCRIPTION,
                "Describe the drink.",
                None,
                "Describe+Drink",
                None,
                "The lemonade is cold and sweet.",
                "Say how the lemonade tastes.",
            ),
        ],
        "roleplay": {
            "title": "Lemonade Stand",
            "description": "Help Lina sell lemonade to a thirsty friend.",
            "character_name": "Lina",
            "character_image_url": "https://placehold.co/600x400?text=Lina+Lemonade",
            "opening_message": "Welcome! Would you like some fresh lemonade?",
            "player_goal": "Order lemonade politely and say thank you.",
            "model_answer": "Yes, please. I would like one lemonade. Thank you.",
            "similar_answers": ["Yes, please.", "One lemonade, please.", "Thank you."],
            "hint_sequence": ["Ask for lemonade.", "Use 'please'.", "Say thank you."],
            "required_turns": 2,
        },
    },
    "The Snack Museum": {
        "reading": [
            (1, "Momo visits a museum full of funny snacks.", "Snack+Museum"),
            (2, "A cookie statue smiles beside a chocolate door.", "Cookie+Statue"),
            (3, "Momo sees popcorn clouds above the tiny train.", "Popcorn+Clouds"),
            (4, "At the end, she draws her favorite snack.", "Draw+Snack"),
        ],
        "repeat": [
            (1, "I see a cookie statue.", "Repeat+Cookie"),
            (2, "The popcorn clouds are funny.", "Repeat+Popcorn"),
            (3, "This is my favorite snack.", "Repeat+Favorite"),
        ],
        "description": [
            (
                1,
                DescriptionQuestionType.WORD_GUESS,
                "Fill in the blank.",
                "Momo sees popcorn ____.",
                "Blank+Clouds",
                "clouds",
                "Momo sees popcorn clouds.",
                "Look up in the museum.",
            ),
            (
                2,
                DescriptionQuestionType.WHY_QUESTION,
                "Why does Momo draw a snack?",
                None,
                "Why+Draw",
                None,
                "Momo draws her favorite snack.",
                "Think about what she likes most.",
            ),
        ],
        "roleplay": {
            "title": "Museum Guide",
            "description": "Ask Momo about the snack museum and choose a favorite snack.",
            "character_name": "Momo",
            "character_image_url": "https://placehold.co/600x400?text=Momo+Museum",
            "opening_message": "This museum is full of snacks! Which snack do you like?",
            "player_goal": "Tell Momo your favorite snack and ask one question.",
            "model_answer": "I like cookies. What is your favorite snack?",
            "similar_answers": ["I like cookies.", "What snack do you like?", "My favorite snack is popcorn."],
            "hint_sequence": ["Say your favorite snack.", "Ask Momo a question.", "Use 'What is your favorite?'"],
            "required_turns": 2,
        },
    },
}


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
    chunks = SAMPLE_COURSE_CONTENT.get(book.title, SAMPLE_COURSE_CONTENT["The Dragon Story"])["reading"]
    created = 0
    for step, text, image_text in chunks:
        result = await session.execute(
            select(ReadingChunk).where(
                ReadingChunk.book_id == book.book_id,
                ReadingChunk.step == step,
            )
        )
        chunk = result.scalar_one_or_none()
        if chunk:
            chunk.text = text
            chunk.image_url = f"https://placehold.co/600x400?text={image_text}"
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
    questions = SAMPLE_COURSE_CONTENT.get(book.title, SAMPLE_COURSE_CONTENT["The Dragon Story"])["repeat"]
    created = 0
    for step, target_text, image_text in questions:
        result = await session.execute(
            select(RepeatQuestion).where(
                RepeatQuestion.book_id == book.book_id,
                RepeatQuestion.step == step,
            )
        )
        question = result.scalar_one_or_none()
        if question:
            question.target_text = target_text
            question.image_url = f"https://placehold.co/600x400?text={image_text}"
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
    questions = SAMPLE_COURSE_CONTENT.get(book.title, SAMPLE_COURSE_CONTENT["The Dragon Story"])["description"]
    created = 0
    for step, question_type, instruction, sentence, image_text, blank_word, answer, hint in questions:
        result = await session.execute(
            select(DescriptionQuestion).where(
                DescriptionQuestion.book_id == book.book_id,
                DescriptionQuestion.step == step,
            )
        )
        question = result.scalar_one_or_none()
        if question:
            question.question_type = question_type
            question.instruction = instruction
            question.sentence = sentence
            question.image_url = f"https://placehold.co/600x400?text={image_text}"
            question.page_number = step
            question.source_text = sentence
            question.blank_word = blank_word
            question.answer_sentence = answer
            question.guide_hint = hint
            continue
        session.add(
            DescriptionQuestion(
                book_id=book.book_id,
                step=step,
                question_type=question_type,
                instruction=instruction,
                sentence=sentence,
                image_url=f"https://placehold.co/600x400?text={image_text}",
                page_number=step,
                source_text=sentence,
                blank_word=blank_word,
                answer_sentence=answer,
                guide_hint=hint,
            )
        )
        created += 1
    return created


async def ensure_roleplay_missions(session: AsyncSession, book: Book) -> int:
    content = SAMPLE_COURSE_CONTENT.get(book.title, SAMPLE_COURSE_CONTENT["The Dragon Story"])["roleplay"]
    result = await session.execute(
        select(RoleplayMission).where(
            RoleplayMission.book_id == book.book_id,
        ).order_by(RoleplayMission.mission_id)
    )
    mission = result.scalars().first()
    if mission:
        mission.title = content["title"]
        mission.description = content["description"]
        mission.character_name = content["character_name"]
        mission.character_image_url = content["character_image_url"]
        mission.opening_message = content["opening_message"]
        mission.player_goal = content["player_goal"]
        mission.model_answer = content["model_answer"]
        mission.similar_answers = content["similar_answers"]
        mission.hint_sequence = content["hint_sequence"]
        mission.required_turns = content["required_turns"]
        return 0

    session.add(
        RoleplayMission(
            book_id=book.book_id,
            title=content["title"],
            description=content["description"],
            character_name=content["character_name"],
            character_image_url=content["character_image_url"],
            opening_message=content["opening_message"],
            player_goal=content["player_goal"],
            model_answer=content["model_answer"],
            similar_answers=content["similar_answers"],
            hint_sequence=content["hint_sequence"],
            required_turns=content["required_turns"],
        )
    )
    return 1


async def seed() -> dict[str, int]:
    async with AsyncSessionLocal() as session:
        book, books_created = await ensure_default_books(session)
        seeded_books = [
            row for row in (
                await session.execute(
                    select(Book).where(Book.title.in_(SAMPLE_COURSE_CONTENT.keys()))
                )
            ).scalars().all()
        ]
        result = {
            "books": books_created,
            "reading_chunks": 0,
            "repeat_questions": 0,
            "description_questions": 0,
            "roleplay_missions": 0,
        }
        for seeded_book in seeded_books or [book]:
            result["reading_chunks"] += await ensure_reading_chunks(session, seeded_book)
            result["repeat_questions"] += await ensure_repeat_questions(session, seeded_book)
            result["description_questions"] += await ensure_description_questions(session, seeded_book)
            result["roleplay_missions"] += await ensure_roleplay_missions(session, seeded_book)
        await session.commit()
        return result


async def main() -> None:
    result = await seed()
    print("Seed completed:")
    for name, count in result.items():
        print(f"- {name}: {count} created")


if __name__ == "__main__":
    asyncio.run(main())
