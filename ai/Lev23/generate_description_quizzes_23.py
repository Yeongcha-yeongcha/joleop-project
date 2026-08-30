"""Level 2/3 accepted text JSON에서 Lesson별 묘사 문제 3개를 생성한다.

Usage:
    python3 -m ai.Lev23.generate_description_quizzes_23 \
        outputs/book_level2_accepted_text.json
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from ai.llm_client import generate_text
from scripts.generate_description_quizzes import (
    extract_pages,
    fallback_blank_word,
    parse_json_object,
)
from shared.models import DescriptionType


QUIZ_COUNT = 3
LEVEL_RULES = {
    2: (
        "Create short-sentence situation-description quizzes. Ask what is "
        "happening in the scene. Each expected answer must be one simple, "
        "complete English sentence of 3-10 words, such as 'The boy is running.' "
        "Describe a visible character and action. Do not ask why. Put the most "
        "important visible action word from the answer first in "
        "keywords_for_evaluation."
    ),
    3: (
        "Create scene-description-and-reason quizzes. Ask the child to describe "
        "the visible scene and explain the character's feeling, choice, or action. "
        "Every expected answer must be one complete English sentence containing "
        "'because', such as 'She looks happy because her friend came.' Put the "
        "most important feeling, choice, or action word from the answer first in "
        "keywords_for_evaluation."
    ),
}

DESCRIPTION_QUIZ_PROMPT = """
You are an educational content designer creating English description quizzes
for Korean children ages 5-9 from an existing story lesson.

Create exactly 3 quizzes for Level {level} (AR {ar_level}).
{level_rule}

Requirements:
- Select exactly 3 different source pages.
- Use only facts visibly supported by each selected story sentence.
- Keep questions and answers appropriate for the stated English level.
- Do not introduce characters, actions, objects, or reasons absent from the text.
- keywords_for_evaluation must contain at least one concrete word used in the
  expected answer. Its first item becomes blank_word and must never be null.

Return ONLY valid JSON:
{{
  "quizzes": [
    {{
      "page_number": 1,
      "quiz_question": "...",
      "expected_answer": "...",
      "acceptable_alternative_answers": ["..."],
      "keywords_for_evaluation": ["..."],
      "hint_1": "a short helpful clue",
      "hint_2": "a second short helpful clue"
    }}
  ]
}}

Theme: {theme}
Story pages:
{story_pages}
""".strip()


def valid_answer(answer: str, level: int) -> bool:
    words = answer.split()
    if level == 2:
        return 3 <= len(words) <= 10 and "because" not in answer.casefold()
    return "because" in answer.casefold() and len(words) >= 4


def fallback_answer(text: str, level: int) -> str:
    cleaned = text.strip()
    if level == 2:
        words = cleaned.split()
        return " ".join(words[:10])
    if "because" in cleaned.casefold():
        return cleaned
    return f"{cleaned} because this action helps the story move forward."


def quiz_blank_word(quiz: dict[str, Any], answer: str, source_text: str) -> str:
    """공통 생성기와 같이 첫 평가 키워드를 빈칸 단어로 사용한다."""
    keywords = quiz.get("keywords_for_evaluation") or []
    if isinstance(keywords, list):
        for keyword in keywords:
            candidate = str(keyword or "").strip()
            if candidate:
                return candidate
    return fallback_blank_word(answer) or fallback_blank_word(source_text) or answer


def generate_description_quizzes(lesson: dict[str, Any]) -> list[dict[str, Any]]:
    level = int(lesson.get("level", 0))
    if level not in LEVEL_RULES:
        raise ValueError("Level 2/3 description quizzes require level 2 or 3 input.")

    pages = extract_pages(lesson)
    if len(pages) < QUIZ_COUNT:
        raise ValueError("Each lesson must contain at least 3 usable story pages.")

    page_text = dict(pages)
    story_pages = "\n".join(f"Page {number}: {text}" for number, text in pages)
    prompt = DESCRIPTION_QUIZ_PROMPT.format(
        level=level,
        ar_level={2: "0.9-1.8", 3: "1.8-2.5"}[level],
        level_rule=LEVEL_RULES[level],
        theme=lesson.get("theme", ""),
        story_pages=story_pages,
    )

    try:
        response = generate_text(
            [{"role": "user", "content": prompt}],
            max_tokens=1400,
            temperature=0.2,
        )
        quizzes = parse_json_object(response).get("quizzes", [])
        results: list[dict[str, Any]] = []
        used_pages: set[int] = set()
        for quiz in quizzes:
            if not isinstance(quiz, dict):
                continue
            page_number = int(quiz.get("page_number", 0))
            answer = str(quiz.get("expected_answer") or "").strip()
            if (
                page_number not in page_text
                or page_number in used_pages
                or not valid_answer(answer, level)
            ):
                continue
            blank_word = quiz_blank_word(
                quiz,
                answer,
                page_text[page_number],
            )
            results.append({
                "scene_number": len(results) + 1,
                "page_number": page_number,
                "text": page_text[page_number],
                "image_path": "",
                "desc_type": (
                    DescriptionType.SENTENCE.value
                    if level == 2
                    else DescriptionType.REASON.value
                ),
                "blank_word": blank_word,
                "answer_sentence": answer,
                "guide_hint": str(quiz.get("hint_1") or answer).strip(),
            })
            used_pages.add(page_number)
            if len(results) == QUIZ_COUNT:
                return results
    except Exception as error:
        print(f"Level {level} 묘사 문제 생성 실패, 기본 문제 사용: {error}")

    desc_type = (
        DescriptionType.SENTENCE.value
        if level == 2
        else DescriptionType.REASON.value
    )
    return [
        _fallback_quiz(index, page_number, text, level, desc_type)
        for index, (page_number, text) in enumerate(pages[:QUIZ_COUNT], 1)
    ]


def _fallback_quiz(
    index: int,
    page_number: int,
    text: str,
    level: int,
    desc_type: str,
) -> dict[str, Any]:
    answer = fallback_answer(text, level)
    return {
        "scene_number": index,
        "page_number": page_number,
        "text": text,
        "image_path": "",
        "desc_type": desc_type,
        "blank_word": fallback_blank_word(answer) or fallback_blank_word(text) or answer,
        "answer_sentence": answer,
        "guide_hint": text[: max(1, len(text) // 2)],
    }


def generate_file(input_path: Path, output_path: Path | None = None) -> Path:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("accepted_text JSON must contain a top-level list.")
    output = [
        {
            "level": int(lesson.get("level", 0)),
            "lesson_number": int(lesson.get("lesson_number", 0)),
            "theme": lesson.get("theme", ""),
            "description_scenes": generate_description_quizzes(lesson),
        }
        for lesson in payload
    ]
    destination = output_path or input_path.with_name(
        f"{input_path.stem}_descriptions.json"
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
        description="Generate Level 2/3 description quizzes from accepted text JSON."
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    print(f"Description quizzes: {generate_file(args.input, args.output)}")


if __name__ == "__main__":
    main()
