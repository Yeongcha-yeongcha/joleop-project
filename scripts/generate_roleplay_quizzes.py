"""accepted text JSON에서 레벨별 롤플레이 문제를 생성한다.

Usage:
    python -m scripts.generate_roleplay_quizzes path/to/*_accepted_text.json
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from ai.llm_client import generate_text
from scripts.generate_description_quizzes import extract_pages, parse_json_object
from shared.models import RoleplayTopic
from shared.settings import LEVEL_CONFIGS


ROLEPLAY_MISSION_PROMPT = """
You are creating speaking roleplay missions for Korean children ages 5-9 from
an existing story lesson. Create exactly {mission_count} warm, short missions
for English Level {level}. Infer the recurring characters from the story pages.

Encourage empathy, helping, confidence, and natural speaking. Do not require an
exact sentence, long conversation, abstract reasoning, or frightening conflict.

Return ONLY valid JSON:
{{
  "missions": [
    {{
      "situation_summary": "...",
      "character_name": "...",
      "mission_goal": "...",
      "expected_intent": "...",
      "example_correct_answers": ["..."],
      "hint_1": "...",
      "hint_2": "...",
      "hint_3": "..."
    }}
  ]
}}

Theme: {theme}
Story pages:
{story_pages}
""".strip()


def generate_roleplay_quizzes(lesson: dict[str, Any]) -> list[dict[str, Any]]:
    level = int(lesson.get("level", 1))
    pages = extract_pages(lesson)
    if not pages:
        return []
    count = LEVEL_CONFIGS[level].roleplay_count
    topic = {
        1: RoleplayTopic.INTRO,
        2: RoleplayTopic.DIRECTION,
        3: RoleplayTopic.ESCAPE,
    }[level]
    prompt = ROLEPLAY_MISSION_PROMPT.format(
        mission_count=count,
        level=level,
        theme=lesson.get("theme", ""),
        story_pages="\n".join(f"Page {number}: {text}" for number, text in pages),
    )
    try:
        response = generate_text(
            [{"role": "user", "content": prompt}],
            max_tokens=1200,
            temperature=0.2,
        )
        missions = parse_json_object(response).get("missions", [])
        results = []
        for mission in missions[:count]:
            if not isinstance(mission, dict):
                continue
            answers = mission.get("example_correct_answers") or []
            expected = mission.get("expected_intent") or ""
            hints = [mission.get(f"hint_{number}", "") for number in (1, 2, 3)]
            results.append({
                "scenario_id": f"rp_{level}_{len(results) + 1}",
                "topic": topic.value,
                "level": level,
                "scene_description": mission.get("situation_summary", ""),
                "character_name": mission.get("character_name", "a story character"),
                "player_goal": mission.get("mission_goal", ""),
                "model_answer": answers[0] if answers else expected,
                "hint_sequence": [hint for hint in hints if hint],
            })
        if len(results) == count:
            return results
    except Exception as error:
        print(f"롤플레이 문제 생성 실패, 기본 문제 사용: {error}")

    return [{
        "scenario_id": f"rp_{level}_1",
        "topic": topic.value,
        "level": level,
        "scene_description": pages[0][1],
        "character_name": "a friendly story character",
        "player_goal": "Say something kind and helpful.",
        "model_answer": "I can help you.",
        "hint_sequence": ["Say something kind.", "Offer help.", "Say, I can help you."],
    }]


def generate_file(input_path: Path, output_path: Path | None = None) -> Path:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("accepted_text JSON must contain a top-level list.")
    output = [
        {
            "level": int(lesson.get("level", 1)),
            "lesson_number": int(lesson.get("lesson_number", 0)),
            "theme": lesson.get("theme", ""),
            "roleplay_scenarios": generate_roleplay_quizzes(lesson),
        }
        for lesson in payload
    ]
    destination = output_path or input_path.with_name(
        f"{input_path.stem}_roleplays.json"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp")
    with temporary.open("w", encoding="utf-8") as file:
        json.dump(output, file, ensure_ascii=False, indent=2)
        file.flush()
        os.fsync(file.fileno())
    temporary.replace(destination)
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate roleplay quizzes from accepted text JSON.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    print(f"Roleplay quizzes: {generate_file(args.input, args.output)}")


if __name__ == "__main__":
    main()
