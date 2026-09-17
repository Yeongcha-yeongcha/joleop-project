"""
Generate iPad 4:3 tablet images from stored lesson image prompts.

This does not regenerate story text. It only reads an existing judged lesson JSON
and writes pXX-tablet.webp files into frontend/public/images/pages.

Example:
    python -m scripts.generate_tablet_images \
      --source-json outputs/run_20260903_114105_819434/qwen_judged_lessons.json \
      --level 1 --lesson 1 --limit 1
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ai.image_generator import generate_tablet_image_from_prompt
from shared.settings import TABLET_IMAGE_SUFFIX


def load_lessons(source_json: Path) -> list[dict[str, Any]]:
    payload = json.loads(source_json.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and isinstance(payload.get("accepted"), list):
        return payload["accepted"]
    if isinstance(payload, list):
        return payload
    raise ValueError(f"Unsupported lesson JSON shape: {source_json}")


def lesson_number(item: dict[str, Any]) -> int:
    lesson = item.get("lesson")
    if isinstance(lesson, dict) and isinstance(lesson.get("episode"), int):
        return int(lesson["episode"])
    if isinstance(item.get("lesson_number"), int):
        return int(item["lesson_number"])
    return 0


def lesson_level(item: dict[str, Any]) -> int:
    lesson = item.get("lesson")
    if isinstance(lesson, dict) and isinstance(lesson.get("level"), int):
        return int(lesson["level"])
    if isinstance(item.get("level"), int):
        return int(item["level"])
    return 0


def lesson_pages(item: dict[str, Any]) -> list[dict[str, Any]]:
    lesson = item.get("lesson")
    if isinstance(lesson, dict) and isinstance(lesson.get("pages"), list):
        return lesson["pages"]
    return []


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate pXX-tablet.webp files from stored image prompts."
    )
    parser.add_argument("--source-json", required=True, help="Judged lesson JSON containing image_prompt values.")
    parser.add_argument(
        "--pages-dir",
        default="frontend/public/images/pages",
        help="Public pages image folder.",
    )
    parser.add_argument("--level", type=int, help="Only generate this level.")
    parser.add_argument("--lesson", type=int, help="Only generate this lesson number.")
    parser.add_argument("--limit", type=int, help="Only generate first N matching pages.")
    parser.add_argument("--overwrite", action="store_true", help="Regenerate existing tablet files.")
    parser.add_argument(
        "--allow-missing-source",
        action="store_true",
        help="Generate even if matching mobile pXX.webp is missing.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print planned outputs without calling ComfyUI.")
    args = parser.parse_args()

    source_json = Path(args.source_json).expanduser().resolve()
    pages_dir = Path(args.pages_dir).expanduser().resolve()
    lessons = load_lessons(source_json)

    jobs: list[tuple[str, Path]] = []
    for item in sorted(lessons, key=lambda value: (lesson_level(value), lesson_number(value))):
        level = lesson_level(item)
        lesson_no = lesson_number(item)
        if args.level is not None and level != args.level:
            continue
        if args.lesson is not None and lesson_no != args.lesson:
            continue

        folder = pages_dir / f"level{level}" / f"lesson{lesson_no:02d}"
        for page in lesson_pages(item):
            page_number = int(page.get("page_number") or 0)
            image_prompt = str(page.get("image_prompt") or "").strip()
            if page_number <= 0 or not image_prompt:
                continue

            source_image = folder / f"p{page_number:02d}.webp"
            target_image = folder / f"p{page_number:02d}{TABLET_IMAGE_SUFFIX}.webp"
            if not args.allow_missing_source and not source_image.exists():
                continue
            if target_image.exists() and not args.overwrite:
                continue
            jobs.append((image_prompt, target_image))

    if args.limit is not None:
        jobs = jobs[: max(0, args.limit)]

    if not jobs:
        print("No tablet image jobs found.")
        return

    print(f"Found {len(jobs)} tablet image job(s).")
    for index, (image_prompt, target_image) in enumerate(jobs, start=1):
        print(f"[{index}/{len(jobs)}] {target_image}")
        if args.dry_run:
            continue
        target_image.parent.mkdir(parents=True, exist_ok=True)
        generate_tablet_image_from_prompt(image_prompt, str(target_image))

    print("Done.")


if __name__ == "__main__":
    main()
