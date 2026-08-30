"""main_theme 하나로 Level 1용 10-Lesson content plan을 생성한다.

Usage:
    python3 -m scripts.generate_content_plan \
        --main-theme "friendship and courage" \
        --output plans/my_book_plan.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from ai.llm_client import generate_text
from shared.settings import MODELS


TOTAL_LESSONS = 10
FIXED_PROTAGONIST = "Popo the lion"
FIXED_CHARACTERS = [
    "Popo the lion",
    "Toto the rabbit",
    "Pipi the parrot",
    "Gigi the giraffe",
    "Momo the mole",
]

CONTENT_PLAN_PROMPT = """
You are a senior children's storybook planner.

Create one canonical Level 1 English storybook for Korean children ages 5-9.
The user provides only a main theme. You must create exactly 10 causally
connected lesson events using the fixed cast below.

Main theme: {main_theme}
Child age: {age}

Book rules:
- This is one continuous story, not 10 separate stories.
- Lesson 1 introduces the protagonist, recurring world, memorable object,
  book-wide goal, and first child-safe problem.
- Lessons 2-9 each contain a different child-engaging central event that
  advances the same goal.
- Lesson 10 resolves the goal and gives the recurring characters a warm ending.
- Preserve characters, important objects, locations, event order, and causality.
- Do not solve the main problem before Lesson 10.
- Keep the story emotionally safe, visual, playful, and suitable for ages 5-9.

Event rules for every episode beat:
- Include a hook, unique central event, protagonist action or choice, concrete
  consequence, and causal connection to the next lesson.
- Vary discoveries, obstacles, choices, mistakes, rescues, transformations,
  arrivals, puzzles, plans, and celebrations.
- Do not repeat the same walking, searching, asking, or helping pattern.
- Avoid unrelated side stories and disposable characters.

Character rules:
- The protagonist is always Popo the lion.
- The complete cast is exactly these five animals: Popo the lion, Toto the
  rabbit, Pipi the parrot, Gigi the giraffe, and Momo the mole.
- All five characters must appear in every book and keep these exact names and
  animal species throughout the plan.
- Do not add any other character, including unnamed animals, people, crowds,
  narrators acting as characters, background characters, or one-off helpers.
- Objects, plants, weather, and locations must not talk, act like characters,
  or be given names.
- Set "protagonist" to exactly "Popo the lion".
- Set "recurring_characters" to exactly
  ["Popo the lion", "Toto the rabbit", "Pipi the parrot",
  "Gigi the giraffe", "Momo the mole"] in that order.

Return ONLY valid JSON with this exact shape:
{{
  "story_title": "...",
  "protagonist": "Popo the lion",
  "story_idea": "one concise sentence describing the full story",
  "book_goal": "...",
  "memorable_object": "...",
  "recurring_characters": ["..."],
  "recurring_locations": ["..."],
  "episode_beats": [
    "Lesson 1 beginning: ...",
    "Lesson 2 development: ...",
    "...",
    "Lesson 10 ending: ..."
  ]
}}

The episode_beats array must contain exactly 10 non-empty strings.
Do not use markdown or write anything outside the JSON.
"""


def parse_json_object(text: str) -> dict[str, Any]:
    cleaned = re.sub(r"```json|```", "", text).strip()
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise
        value = json.loads(match.group(0))
    if not isinstance(value, dict):
        raise ValueError("Llama output must be a JSON object.")
    return value


def validate_outline(outline: dict[str, Any]) -> None:
    required = ["story_title", "protagonist", "story_idea", "episode_beats"]
    missing = [key for key in required if not outline.get(key)]
    if missing:
        raise ValueError(f"Outline is missing: {', '.join(missing)}")

    if outline["protagonist"] != FIXED_PROTAGONIST:
        raise ValueError(f"protagonist must be exactly {FIXED_PROTAGONIST!r}.")
    if outline.get("recurring_characters") != FIXED_CHARACTERS:
        raise ValueError(
            "recurring_characters must contain only the five fixed characters "
            "in the required order."
        )

    beats = outline["episode_beats"]
    if not isinstance(beats, list) or len(beats) != TOTAL_LESSONS:
        raise ValueError("episode_beats must contain exactly 10 items.")
    if any(not isinstance(beat, str) or not beat.strip() for beat in beats):
        raise ValueError("Every episode beat must be a non-empty string.")

    if not beats[0].lstrip().lower().startswith("lesson 1 beginning"):
        raise ValueError("The first beat must start with 'Lesson 1 beginning'.")
    if not beats[-1].lstrip().lower().startswith("lesson 10 ending"):
        raise ValueError("The final beat must start with 'Lesson 10 ending'.")


def generate_content_plan(
    main_theme: str,
    *,
    age: int = 3,
    max_attempts: int = 2,
) -> dict[str, Any]:
    prompt = CONTENT_PLAN_PROMPT.format(main_theme=main_theme, age=age)
    last_error = "No valid outline returned."

    for attempt in range(1, max_attempts + 1):
        try:
            response = generate_text(
                [{"role": "user", "content": prompt}],
                model=MODELS.story_model,
                max_tokens=1800,
                temperature=0.45,
            )
            outline = parse_json_object(response)
            # Character identities are application-owned constants. Normalize
            # model output before validation so harmless additions such as a
            # visual description do not make the whole plan fail.
            outline["protagonist"] = FIXED_PROTAGONIST
            outline["recurring_characters"] = FIXED_CHARACTERS.copy()
            validate_outline(outline)
            break
        except Exception as error:
            last_error = str(error)
            print(f"Plan 생성 재시도 {attempt}/{max_attempts}: {last_error}")
    else:
        raise RuntimeError(f"Content plan 생성 실패: {last_error}")

    return {
        "book_id": "book1",
        "start_episode": 1,
        "level": 1,
        "age": age,
        "protagonist": FIXED_PROTAGONIST,
        "main_theme": main_theme,
        "story_title": str(outline["story_title"]).strip(),
        "story_idea": str(outline["story_idea"]).strip(),
        "book_goal": str(outline.get("book_goal", "")).strip(),
        "memorable_object": str(outline.get("memorable_object", "")).strip(),
        "recurring_characters": FIXED_CHARACTERS.copy(),
        "recurring_locations": outline.get("recurring_locations", []),
        "min_score": 70,
        "target_lessons": TOTAL_LESSONS,
        "quality_retries": 1,
        "max_total_attempts_multiplier": 3,
        "generate_images": False,
        "generate_tts": False,
        "output_path": "qwen_judged_lessons.json",
        "episode_beats": [beat.strip() for beat in outline["episode_beats"]],
    }


def write_plan(plan: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("x", encoding="utf-8") as file:
        json.dump(plan, file, ensure_ascii=False, indent=2)
        file.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a 10-lesson Level 1 content plan from a main theme."
    )
    parser.add_argument("--main-theme", required=True, help="Main theme for the book.")
    parser.add_argument("--age", type=int, default=3, help="Target child age (default: 3).")
    parser.add_argument(
        "--output",
        default="plans/content_plan.generated.json",
        help="New JSON path; an existing file will not be overwritten.",
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=2,
        help="Maximum outline generation attempts (default: 2).",
    )
    args = parser.parse_args()

    if not args.main_theme.strip():
        parser.error("--main-theme must not be empty.")
    if args.max_attempts < 1:
        parser.error("--max-attempts must be at least 1.")

    output_path = Path(args.output)
    if output_path.exists():
        parser.error(f"Output already exists: {output_path}. Choose another path.")

    print(f"[Content plan 생성] theme={args.main_theme}")
    plan = generate_content_plan(
        args.main_theme.strip(),
        age=args.age,
        max_attempts=args.max_attempts,
    )
    write_plan(plan, output_path)
    print(f"완료: {output_path}")
    print(f"제목: {plan['story_title']}")
    print(f"주인공: {plan['protagonist']}")
    print(f"Lesson 수: {len(plan['episode_beats'])}")


if __name__ == "__main__":
    main()
