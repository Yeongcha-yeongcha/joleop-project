"""description JSON의 모든 문장에서 빈칸 복습 데이터를 생성한다.

Usage:
    python3 -m ai.Review.generate_review_data

    python3 -m ai.Review.generate_review_data \
        outputs/test17_character/qwen_judged_lessons_accepted_text_descriptions.json

기본 출력 파일명은 ``<입력 파일명>_review.json``이다.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

from scripts.generate_description_quizzes import fallback_blank_word


DEFAULT_INPUT = Path(
    "outputs/test17_character/"
    "qwen_judged_lessons_accepted_text_descriptions.json"
)


def make_blank_text(text: str, blank_word: str) -> str:
    """문장 안의 blank_word를 백엔드용 ``{blank_word}`` 표기로 바꾼다."""
    source = text.strip()
    answer = blank_word.strip()
    if not source:
        raise ValueError("text must not be empty.")
    if not answer:
        raise ValueError("blank_word must not be empty.")

    # 구나 하이픈 단어도 처리하되, 다른 단어의 일부는 지우지 않는다.
    pattern = re.compile(
        rf"(?<![A-Za-z]){re.escape(answer)}(?![A-Za-z])",
        flags=re.IGNORECASE,
    )
    placeholder = "{" + answer + "}"
    blank_text, count = pattern.subn(lambda _: placeholder, source)
    if count == 0:
        raise ValueError(f"blank_word {answer!r} does not occur in text {source!r}.")
    return blank_text


def normalize_scene(scene: dict[str, Any]) -> dict[str, Any]:
    """기존 문제 필드를 보존하면서 blank_text를 덧붙인다."""
    result = dict(scene)
    result.pop("answer_sentence", None)
    result.pop("answr_sentence", None)
    result.pop("guide_hint", None)
    text = str(result.get("text") or "").strip()
    blank_word = str(result.get("blank_word") or "").strip()

    # 모델이 원문에 없는 활용형을 고른 경우(예: walking / walked), 원문에
    # 실제로 있는 단어로 교체하여 빈칸과 정답이 반드시 서로 대응하게 한다.
    if not re.search(
        rf"(?<![A-Za-z]){re.escape(blank_word)}(?![A-Za-z])",
        text,
        flags=re.IGNORECASE,
    ):
        blank_word = fallback_blank_word(text) or ""
        if not blank_word:
            raise ValueError(f"Could not choose a blank word from {text!r}.")
        result["blank_word"] = blank_word

    result["blank_text"] = make_blank_text(text, blank_word)
    return result


def build_review_data(payload: list[Any]) -> list[dict[str, Any]]:
    """모든 description scene을 빠짐없이 복습 데이터로 변환한다."""
    output: list[dict[str, Any]] = []
    for lesson in payload:
        if not isinstance(lesson, dict):
            raise ValueError("Every lesson must be a JSON object.")
        scenes = lesson.get("description_scenes")
        if scenes is None:
            raise ValueError(
                "Each lesson must contain description_scenes. "
                "Use a *_descriptions.json input file."
            )
        if not isinstance(scenes, list):
            raise ValueError("description_scenes must be a list.")

        output.append({
            "level": int(lesson.get("level", 1)),
            "lesson_number": int(lesson.get("lesson_number", 0)),
            "theme": lesson.get("theme", ""),
            "review_scenes": [normalize_scene(scene) for scene in scenes],
        })
    return output


def generate_file(input_path: Path, output_path: Path | None = None) -> Path:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Input JSON must contain a top-level list.")

    destination = output_path or input_path.with_name(
        f"{input_path.stem}_review.json"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp")
    with temporary.open("w", encoding="utf-8") as file:
        json.dump(build_review_data(payload), file, ensure_ascii=False, indent=2)
        file.flush()
        os.fsync(file.fileno())
    temporary.replace(destination)
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate review data from every scene in a descriptions JSON."
    )
    parser.add_argument("input", nargs="?", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    print(f"Review data: {generate_file(args.input, args.output)}")


if __name__ == "__main__":
    main()
