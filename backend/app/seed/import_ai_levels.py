import argparse
import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

from app.models import Difficulty
from app.seed.import_ai_content import import_content

WORKSPACE_DIR = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUTS_DIR = WORKSPACE_DIR / "outputs" / "test17_character"


LEVEL_IMPORTS = [
    {
        "level": 1,
        "difficulty": Difficulty.BEGINNER.value,
        "title": "",
        "accepted_text": "qwen_judged_lessons_accepted_text.json",
        "description_file": "qwen_judged_lessons_accepted_text_descriptions.json",
        "roleplay_file": "qwen_judged_lessons_accepted_text_roleplays.json",
        "display_order": 0,
        "cover_image_url": "/images/BookSample_A.png",
        "cover_color": "#F7C948",
    },
    {
        "level": 2,
        "difficulty": Difficulty.INTERMEDIATE.value,
        "title": "",
        "accepted_text": "qwen_judged_lessons_level2_accepted_text.json",
        "description_file": "qwen_judged_lessons_level2_accepted_text_descriptions.json",
        "roleplay_file": "qwen_judged_lessons_level2_accepted_text_roleplays.json",
        "display_order": 0,
        "cover_image_url": "/images/BookSample_B.png",
        "cover_color": "#5FB67A",
    },
    {
        "level": 3,
        "difficulty": Difficulty.ADVANCED.value,
        "title": "",
        "accepted_text": "qwen_judged_lessons_level3_accepted_text.json",
        "description_file": "qwen_judged_lessons_level3_accepted_text_descriptions.json",
        "roleplay_file": "qwen_judged_lessons_level3_accepted_text_roleplays.json",
        "display_order": 0,
        "cover_image_url": "/images/BookSample_C.png",
        "cover_color": "#6F83D8",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import all checked AI story levels into the app DB.")
    parser.add_argument(
        "--outputs-dir",
        default=str(DEFAULT_OUTPUTS_DIR),
        help="Directory containing qwen judged accepted_text JSON files.",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    outputs_dir = Path(args.outputs_dir)
    results = []
    for item in LEVEL_IMPORTS:
        result = await import_content(
            SimpleNamespace(
                accepted_text=str(outputs_dir / item["accepted_text"]),
                description_file=str(outputs_dir / item["description_file"]),
                roleplay_file=str(outputs_dir / item["roleplay_file"]),
                book_id=None,
                title=item["title"],
                difficulty=item["difficulty"],
                display_order=item["display_order"],
                cover_image_url=item["cover_image_url"],
                cover_color=item["cover_color"],
            )
        )
        results.append({**item, **result})

    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
