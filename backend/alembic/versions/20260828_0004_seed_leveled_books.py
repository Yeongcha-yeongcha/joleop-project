"""seed leveled books

Revision ID: 20260828_0004
Revises: 20260824_0003
Create Date: 2026-08-28 10:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260828_0004"
down_revision: str | None = "20260824_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


leveled_books = [
    {
        "title": "The Dragon Story",
        "lesson_name": "Lesson 1",
        "difficulty": "BEGINNER",
        "cover_image_url": "/images/BookSample_A.png",
        "display_order": 1,
    },
    {
        "title": "Fresh Lemonade!",
        "lesson_name": "Lesson 1",
        "difficulty": "BEGINNER",
        "cover_image_url": "/images/BookSample_B.png",
        "display_order": 2,
    },
    {
        "title": "The Snack Museum",
        "lesson_name": "Lesson 1",
        "difficulty": "BEGINNER",
        "cover_image_url": "/images/BookSample_C.png",
        "display_order": 3,
    },
    {
        "title": "Bad Morning",
        "lesson_name": "Lesson 1",
        "difficulty": "BEGINNER",
        "cover_image_url": None,
        "display_order": 4,
    },
    {
        "title": "Little Star",
        "lesson_name": "Lesson 1",
        "difficulty": "BEGINNER",
        "cover_image_url": None,
        "display_order": 5,
    },
    {
        "title": "Sunny Day",
        "lesson_name": "Lesson 1",
        "difficulty": "INTERMEDIATE",
        "cover_image_url": None,
        "display_order": 6,
    },
    {
        "title": "Magic Forest",
        "lesson_name": "Lesson 1",
        "difficulty": "INTERMEDIATE",
        "cover_image_url": None,
        "display_order": 7,
    },
    {
        "title": "Ocean Friends",
        "lesson_name": "Lesson 1",
        "difficulty": "INTERMEDIATE",
        "cover_image_url": None,
        "display_order": 8,
    },
    {
        "title": "Cloud Castle",
        "lesson_name": "Lesson 1",
        "difficulty": "INTERMEDIATE",
        "cover_image_url": None,
        "display_order": 9,
    },
    {
        "title": "Rainbow Bridge",
        "lesson_name": "Lesson 1",
        "difficulty": "INTERMEDIATE",
        "cover_image_url": None,
        "display_order": 10,
    },
    {
        "title": "Tiny Robot",
        "lesson_name": "Lesson 1",
        "difficulty": "ADVANCED",
        "cover_image_url": None,
        "display_order": 11,
    },
    {
        "title": "Jungle Race",
        "lesson_name": "Lesson 1",
        "difficulty": "ADVANCED",
        "cover_image_url": None,
        "display_order": 12,
    },
    {
        "title": "Moon Cake",
        "lesson_name": "Lesson 1",
        "difficulty": "ADVANCED",
        "cover_image_url": None,
        "display_order": 13,
    },
    {
        "title": "Deep Sea",
        "lesson_name": "Lesson 1",
        "difficulty": "ADVANCED",
        "cover_image_url": None,
        "display_order": 14,
    },
    {
        "title": "Star Patrol",
        "lesson_name": "Lesson 1",
        "difficulty": "ADVANCED",
        "cover_image_url": None,
        "display_order": 15,
    },
]


def upgrade() -> None:
    connection = op.get_bind()
    for book in leveled_books:
        exists = connection.execute(
            sa.text(
                """
                SELECT 1 FROM books
                WHERE title = :title
                  AND lesson_name = :lesson_name
                  AND difficulty = CAST(:difficulty AS difficulty)
                LIMIT 1
                """
            ),
            book,
        ).first()
        if exists:
            connection.execute(
                sa.text(
                    """
                    UPDATE books
                    SET cover_image_url = :cover_image_url,
                        display_order = :display_order
                    WHERE title = :title
                      AND lesson_name = :lesson_name
                      AND difficulty = CAST(:difficulty AS difficulty)
                    """
                ),
                book,
            )
            continue
        connection.execute(
            sa.text(
                """
                INSERT INTO books (
                    title,
                    lesson_name,
                    difficulty,
                    cover_image_url,
                    display_order
                )
                VALUES (
                    :title,
                    :lesson_name,
                    CAST(:difficulty AS difficulty),
                    :cover_image_url,
                    :display_order
                )
                """
            ),
            book,
        )


def downgrade() -> None:
    titles = [book["title"] for book in leveled_books]
    op.get_bind().execute(
        sa.text("DELETE FROM books WHERE title IN :titles").bindparams(
            sa.bindparam("titles", expanding=True)
        ),
        {"titles": titles},
    )
