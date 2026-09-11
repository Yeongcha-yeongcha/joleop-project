import asyncio


async def seed() -> dict[str, int]:
    """No-op seed.

    Real story content should come from the database, typically via
    app.seed.import_ai_content or direct DB imports.
    """
    return {
        "books": 0,
        "reading_chunks": 0,
        "repeat_questions": 0,
        "description_questions": 0,
        "roleplay_missions": 0,
    }


async def main() -> None:
    result = await seed()
    print("Seed skipped: mock story data has been removed.")
    for name, count in result.items():
        print(f"- {name}: {count} created")


if __name__ == "__main__":
    asyncio.run(main())
