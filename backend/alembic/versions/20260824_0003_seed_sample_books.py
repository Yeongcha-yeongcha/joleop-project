"""seed sample books

Revision ID: 20260824_0003
Revises: 20260824_0002
Create Date: 2026-08-24 02:10:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260824_0003"
down_revision: str | None = "20260824_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


sample_books = [
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
        "difficulty": "BEGINNER",
        "cover_image_url": None,
        "display_order": 6,
    },
]


def upgrade() -> None:
    books_table = sa.table(
        "books",
        sa.column("title", sa.String),
        sa.column("lesson_name", sa.String),
        sa.column("difficulty", sa.String),
        sa.column("cover_image_url", sa.String),
        sa.column("display_order", sa.Integer),
    )
    connection = op.get_bind()
    for book in sample_books:
        exists = connection.execute(
            sa.text(
                """
                SELECT 1 FROM books
                WHERE title = :title
                  AND lesson_name = :lesson_name
                  AND difficulty = :difficulty
                LIMIT 1
                """
            ),
            {
                "title": book["title"],
                "lesson_name": book["lesson_name"],
                "difficulty": book["difficulty"],
            },
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
                      AND difficulty = :difficulty
                    """
                ),
                book,
            )
            continue
        op.bulk_insert(books_table, [book])


def downgrade() -> None:
    titles = [book["title"] for book in sample_books]
    op.get_bind().execute(
        sa.text("DELETE FROM books WHERE title IN :titles").bindparams(
            sa.bindparam("titles", expanding=True)
        ),
        {"titles": titles},
    )
