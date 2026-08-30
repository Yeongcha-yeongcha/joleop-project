"""Level 2/3 accepted text JSON에서 레벨별 롤플레이 퀴즈를 생성한다.

Usage:
    python3 -m ai.Lev23.generate_roleplay_quizzes_23         
    outputs/test17_character/qwen_judged_lessons_level2_accepted_text.json 
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


LEVEL_RULES = {
    2: (
        "Create one short situational roleplay focused on talking with a friend, "
        "expressing a feeling, or asking for simple help. Frame it as asking a "
        "friendly hunter for directions. The child should produce one short, "
        "natural request or feeling sentence. Keep the task concrete and solvable "
        "in a single speaking turn."
    ),
    3: (
        "Create two short story-based roleplays that include a simple problem and "
        "a meaningful choice. Frame them as steps in escaping safely from a "
        "ballroom. Each mission must require the child to explain a choice, ask "
        "for help, suggest a solution, or make a safe plan in one or two sentences. "
        "The two missions must be different stages of the situation."
    ),
}


ROLEPLAY_MISSION_PROMPT = """
You are creating speaking roleplay missions for Korean children ages 5-9 from
an existing story lesson. Create exactly {mission_count} warm, short missions
for English Level {level}. Infer suitable recurring characters and concrete
details from the story pages.

{level_rule}

Requirements:
- Ground each mission in the supplied story's characters, emotions, objects, or
  events while using the required roleplay frame.
- Encourage empathy, helping, confidence, choice, and natural speaking.
- Do not require an exact sentence, a long conversation, abstract reasoning, or
  frightening conflict.
- Make model_answer directly achieve mission_goal and match expected_intent.
- Provide exactly three unique similar_answers for every mission. They must
  express the same intent as model_answer with natural but different wording.
- Provide three progressively more specific, child-friendly hints.

Return ONLY valid JSON:
{{
  "missions": [
    {{
      "situation_summary": "...",
      "character_name": "...",
      "mission_goal": "...",
      "expected_intent": "...",
      "model_answer": "one clear model response",
      "similar_answers": [
        "same intent with different words 1",
        "same intent with different words 2",
        "same intent with different words 3"
      ],
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


def normalize_similar_answers(
    mission: dict[str, Any],
    model_answer: str,
) -> list[str]:
    """현재 형식과 예전 생성 형식을 모두 동일한 출력으로 정규화한다."""
    legacy_answers = mission.get("example_correct_answers") or []
    similar_answers = mission.get("similar_answers") or []
    if not similar_answers:
        similar_answers = (
            legacy_answers[1:]
            + (mission.get("acceptable_alternative_answers") or [])
        )
    return list(dict.fromkeys(
        str(answer).strip()
        for answer in similar_answers
        if str(answer).strip() and str(answer).strip() != model_answer
    ))[:3]


def fallback_roleplays(
    level: int,
    pages: list[tuple[int, str]],
) -> list[dict[str, Any]]:
    """LLM 응답이 잘못되어도 레벨별 횟수와 형식을 보장한다."""
    if level == 2:
        return [{
            "scenario_id": "rp_2_1",
            "topic": RoleplayTopic.DIRECTION.value,
            "level": 2,
            "scene_description": (
                f"You meet a friendly hunter while trying to reach the place in "
                f"the story: {pages[0][1]}"
            ),
            "character_name": "friendly hunter",
            "player_goal": "Ask the hunter how to get there.",
            "model_answer": "Can you show me the way, please?",
            "similar_answers": [
                "Could you tell me which way to go?",
                "Please help me find the way.",
                "Do you know how I can get there?",
            ],
            "hint_sequence": [
                "Politely ask for help.",
                "Ask which way to go.",
                "Start with, Can you show me...",
            ],
        }]

    stages = [
        {
            "scene": "You notice a safe side door while music fills the ballroom.",
            "character": "your story friend",
            "goal": "Suggest using the side door to leave safely.",
            "answer": "Let's leave safely through the side door.",
            "similar": [
                "We can use the side door to get out.",
                "Let's go out through that safe door.",
                "I think we should take the side door.",
            ],
            "hints": [
                "Make a safe choice.",
                "Suggest which door to use.",
                "Start with, Let's leave safely...",
            ],
        },
        {
            "scene": "Your friend is nervous and needs help leaving the ballroom.",
            "character": "your story friend",
            "goal": "Offer help and make a plan to leave together.",
            "answer": "Stay with me, and we can leave together.",
            "similar": [
                "Come with me so we can get out safely.",
                "I will help you leave the ballroom.",
                "Let's stay together and find the exit.",
            ],
            "hints": [
                "Help your worried friend.",
                "Say you will leave together.",
                "Start with, Stay with me...",
            ],
        },
    ]
    return [
        {
            "scenario_id": f"rp_3_{index}",
            "topic": RoleplayTopic.ESCAPE.value,
            "level": 3,
            "scene_description": (
                f"{stage['scene']} Story context: "
                f"{pages[min(index - 1, len(pages) - 1)][1]}"
            ),
            "character_name": stage["character"],
            "player_goal": stage["goal"],
            "model_answer": stage["answer"],
            "similar_answers": stage["similar"],
            "hint_sequence": stage["hints"],
        }
        for index, stage in enumerate(stages, 1)
    ]


def generate_roleplay_quizzes(lesson: dict[str, Any]) -> list[dict[str, Any]]:
    level = int(lesson.get("level", 0))
    if level not in LEVEL_RULES:
        raise ValueError("Level 2/3 roleplay quizzes require level 2 or 3 input.")

    pages = extract_pages(lesson)
    if not pages:
        return []

    count = LEVEL_CONFIGS[level].roleplay_count
    topic = (
        RoleplayTopic.DIRECTION
        if level == 2
        else RoleplayTopic.ESCAPE
    )
    prompt = ROLEPLAY_MISSION_PROMPT.format(
        mission_count=count,
        level=level,
        level_rule=LEVEL_RULES[level],
        theme=lesson.get("theme", ""),
        story_pages="\n".join(
            f"Page {number}: {text}" for number, text in pages
        ),
    )

    try:
        response = generate_text(
            [{"role": "user", "content": prompt}],
            max_tokens=1600,
            temperature=0.2,
        )
        missions = parse_json_object(response).get("missions", [])
        results: list[dict[str, Any]] = []
        for mission in missions[:count]:
            if not isinstance(mission, dict):
                continue
            legacy_answers = mission.get("example_correct_answers") or []
            expected = mission.get("expected_intent") or ""
            model_answer = str(
                mission.get("model_answer")
                or (legacy_answers[0] if legacy_answers else expected)
            ).strip()
            similar_answers = normalize_similar_answers(mission, model_answer)
            if not model_answer or len(similar_answers) != 3:
                continue
            hints = [
                str(mission.get(f"hint_{number}") or "").strip()
                for number in (1, 2, 3)
            ]
            results.append({
                "scenario_id": f"rp_{level}_{len(results) + 1}",
                "topic": topic.value,
                "level": level,
                "scene_description": str(
                    mission.get("situation_summary") or ""
                ).strip(),
                "character_name": str(
                    mission.get("character_name") or "a story character"
                ).strip(),
                "player_goal": str(mission.get("mission_goal") or "").strip(),
                "model_answer": model_answer,
                "similar_answers": similar_answers,
                "hint_sequence": [hint for hint in hints if hint],
            })
        if len(results) == count:
            return results
    except Exception as error:
        print(f"Level {level} 롤플레이 문제 생성 실패, 기본 문제 사용: {error}")

    return fallback_roleplays(level, pages)


def generate_file(input_path: Path, output_path: Path | None = None) -> Path:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("accepted_text JSON must contain a top-level list.")
    output = [
        {
            "level": int(lesson.get("level", 0)),
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
    parser = argparse.ArgumentParser(
        description="Generate Level 2/3 roleplay quizzes from accepted text JSON."
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    print(f"Roleplay quizzes: {generate_file(args.input, args.output)}")


if __name__ == "__main__":
    main()
