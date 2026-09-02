"""Generate every story and quiz artifact from one saved Level 1 book plan.

This module orchestrates the existing generators by importing their Python
functions; it does not launch them as subprocesses.

Usage:
    python -m scripts.generate_all_content plans/test1_book_plan.json
    python -m scripts.generate_all_content plans/test1_book_plan.json \
        --run-name test1_all
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from ai.Lev23 import generate_description_quizzes_23
from ai.Lev23 import generate_roleplay_quizzes_23
from ai.Lev23 import story_generator_23
from scripts import generate_description_quizzes
from scripts import generate_lessons
from scripts import generate_roleplay_quizzes


def _write_json(path: Path, payload: Any) -> None:
    """Atomically write a JSON artifact."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.flush()
        os.fsync(file.fileno())
    temporary.replace(path)


def _prepare_run_directory(output_root: Path, run_name: str) -> Path:
    if Path(run_name).name != run_name or run_name in {"", ".", ".."}:
        raise ValueError("run_name must be a single folder name, not a path.")

    run_dir = output_root / run_name
    try:
        run_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError as error:
        raise FileExistsError(
            f"Run folder already exists: {run_dir}. Choose another --run-name."
        ) from error
    (run_dir / "images").mkdir()
    (run_dir / "audio").mkdir()
    return run_dir


def _validate_complete_level(
    lessons: list[dict[str, Any]], level: int, expected: int
) -> None:
    if len(lessons) != expected:
        raise RuntimeError(
            f"Level {level} produced {len(lessons)} accepted lessons; "
            f"{expected} are required before the next stages can run."
        )


async def generate_all(
    plan_path: Path,
    *,
    output_root: Path = Path("outputs"),
    run_name: str | None = None,
    write_story_text: bool = True,
) -> dict[str, Any]:
    """Run Level 1, Level 2/3 rewrites, and all quiz generators."""
    plan = generate_lessons.load_plan(plan_path)
    if "levels" in plan:
        raise ValueError(
            "The all-content pipeline requires a single Level 1 book plan, not "
            "a curriculum plan with a 'levels' array."
        )

    expected_lessons = generate_lessons.get_target_lessons(plan)
    chosen_run_name = (
        run_name
        or plan.get("run_name")
        or datetime.now().strftime("run_%Y%m%d_%H%M%S_%f")
    )
    run_dir = _prepare_run_directory(output_root, chosen_run_name)

    level1_result_path = run_dir / Path(
        plan.get("output_path", "qwen_judged_lessons.json")
    ).name
    level1_accepted_path = level1_result_path.with_name(
        f"{level1_result_path.stem}_accepted_text.json"
    )

    plan["_image_output_dir"] = str(run_dir / "images")
    plan["_audio_output_dir"] = str(run_dir / "audio")
    plan["_checkpoint_path"] = str(level1_result_path)
    plan["_draft_path"] = str(run_dir / "llama_story_drafts.json")

    generate_lessons.write_checkpoint(
        plan,
        {
            "book_id": plan["book_id"],
            "accepted_count": 0,
            "rejected_count": 0,
            "accepted": [],
            "rejected": [],
        },
    )

    try:
        level1_result = await generate_lessons.run_plan(plan)
        _validate_complete_level(
            level1_result.get("accepted", []), 1, expected_lessons
        )
        generate_lessons.write_checkpoint(plan, level1_result, status="completed")
        generate_lessons.set_draft_status(plan, "completed")
    except BaseException as error:
        generate_lessons.mark_checkpoint_stopped(plan, error)
        generate_lessons.set_draft_status(
            plan,
            "interrupted" if isinstance(error, KeyboardInterrupt) else "failed",
        )
        raise

    generate_lessons.write_accepted_text_output(level1_result, level1_result_path)
    if write_story_text:
        generate_lessons.write_story_text_output(level1_result, level1_result_path)

    artifacts: dict[str, str] = {
        "level1_story": str(level1_result_path),
        "level1_accepted_text": str(level1_accepted_path),
        "level1_descriptions": str(
            generate_description_quizzes.generate_file(level1_accepted_path)
        ),
        "level1_roleplays": str(
            generate_roleplay_quizzes.generate_file(level1_accepted_path)
        ),
    }

    accepted_level1, rewrite_plan = story_generator_23.load_inputs(
        level1_accepted_path, plan_path
    )
    for level in story_generator_23.LEVELS:
        rewritten = await story_generator_23.generate_level_book(
            accepted_level1, rewrite_plan, level
        )
        payload = story_generator_23.accepted_text_payload(rewritten, level)
        _validate_complete_level(payload, level, expected_lessons)
        accepted_path = story_generator_23.level_output_path(
            level1_accepted_path, level
        )
        story_generator_23.write_json(accepted_path, payload)

        artifacts[f"level{level}_accepted_text"] = str(accepted_path)
        artifacts[f"level{level}_descriptions"] = str(
            generate_description_quizzes_23.generate_file(accepted_path)
        )
        artifacts[f"level{level}_roleplays"] = str(
            generate_roleplay_quizzes_23.generate_file(accepted_path)
        )

    manifest = {
        "generation_status": "completed",
        "plan": str(plan_path),
        "book_id": plan["book_id"],
        "lesson_count_per_level": expected_lessons,
        "artifacts": artifacts,
    }
    manifest_path = run_dir / "all_content_manifest.json"
    artifacts["manifest"] = str(manifest_path)
    _write_json(manifest_path, manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Generate Level 1-3 stories, description quizzes, and roleplay "
            "quizzes from one Level 1 plan JSON."
        )
    )
    parser.add_argument("plan", type=Path, help="Level 1 plan JSON in plans/.")
    parser.add_argument("--run-name", help="Unique output folder name.")
    parser.add_argument(
        "--output-root", type=Path, default=Path("outputs"),
        help="Parent directory for the run folder (default: outputs).",
    )
    parser.add_argument(
        "--no-story-text", action="store_true",
        help="Do not create the readable Level 1 Markdown story file.",
    )
    args = parser.parse_args()

    manifest = asyncio.run(
        generate_all(
            args.plan,
            output_root=args.output_root,
            run_name=args.run_name,
            write_story_text=not args.no_story_text,
        )
    )
    print("\nAll content generation completed.")
    for name, path in manifest["artifacts"].items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
