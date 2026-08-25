"""accepted text JSON에서 레벨별 묘사 문제를 생성한다.

Usage:
    python -m scripts.generate_description_quizzes path/to/*_accepted_text.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

from ai.llm_client import generate_text
from shared.models import DescriptionType
from shared.settings import LEVEL_CONFIGS


DESCRIPTION_QUIZ_PROMPT = """
You are an educational content designer creating English description quizzes
for Korean children ages 5-9 from an existing story lesson.

Create exactly {quiz_count} quizzes for Level {level} (AR {ar_level}).
{level_instruction}

Choose visually clear pages with concrete actions, colors, objects, animals,
emotions, locations, weather, or body movement. Use different source pages.

Return ONLY valid JSON:
{{
  "quizzes": [
    {{
      "page_number": 1,
      "quiz_question": "...",
      "expected_answer": "...",
      "acceptable_alternative_answers": ["..."],
      "keywords_for_evaluation": ["..."],
      "hint_1": "easy clue about the word's meaning, use, color, shape, or action",
      "hint_2": "a second easy clue about the word itself"
    }}
  ]
}}

Theme: {theme}
Story pages:
{story_pages}
""".strip()


def parse_json_object(text: str) -> dict[str, Any]:
    cleaned = re.sub(r"```(?:json)?|```", "", text).strip()
    decoder = json.JSONDecoder()
    last_error: Exception | None = None
    # 모델이 JSON 뒤에 설명이나 두 번째 JSON을 붙여도 첫 유효 객체만 읽는다.
    for match in re.finditer(r"\{", cleaned):
        try:
            value, _ = decoder.raw_decode(cleaned[match.start():])
        except json.JSONDecodeError as error:
            last_error = error
            continue
        if isinstance(value, dict):
            return value
    if last_error:
        raise last_error
    raise ValueError("Description generator must return a JSON object.")


def extract_pages(lesson: dict[str, Any]) -> list[tuple[int, str]]:
    pages: list[tuple[int, str]] = []
    for page in lesson.get("lesson", []):
        if not isinstance(page, dict) or len(page) != 1:
            continue
        key, text = next(iter(page.items()))
        match = re.fullmatch(r"page(\d+)", str(key), flags=re.IGNORECASE)
        if match and isinstance(text, str) and text.strip():
            pages.append((int(match.group(1)), text.strip()))
    return sorted(pages)


def fallback_blank_word(text: str) -> str | None:
    stopwords = {
        "a", "an", "and", "are", "at", "in", "is", "it", "of", "on",
        "the", "to", "was", "were", "with", "she", "he", "they",
    }
    words = re.findall(r"[A-Za-z]+", text)
    candidates = [word for word in words if word.casefold() not in stopwords]
    return candidates[-1] if candidates else (words[-1] if words else None)


def valid_level1_hint(hint: Any, *, blank_word: str) -> str | None:
    """정답 노출과 위치 안내가 없는 뜻풀이 힌트인지 검사한다."""
    candidate = str(hint or "").strip()
    forbidden = re.compile(
        r"\b(?:picture|image|scene|illustration|page|look|see)\b"
        r"|starts? with|first letter|rhymes? with|_+",
        flags=re.IGNORECASE,
    )
    contains_answer = re.search(
        rf"\b{re.escape(blank_word)}\b", candidate, flags=re.IGNORECASE
    )
    if candidate and not forbidden.search(candidate) and not contains_answer:
        return candidate
    return None


def generate_level1_meaning_hint(blank_word: str, source_text: str) -> str:
    """잘못된 힌트를 단어의 쉬운 영어 뜻풀이로 다시 생성한다."""
    prompt = f"""Explain this English word to a Korean child age 5-9.

Word: {blank_word}
Story context: {source_text}

Write one very short, easy English meaning clue.
- Explain what the word means, does, or is used for.
- Do not use the answer word itself.
- Do not mention a picture, image, scene, illustration, page, looking, or seeing.
- Do not use a fill-in-the-blank sentence.

Return ONLY JSON: {{"hint": "..."}}"""
    last_error: Exception | None = None
    retry_note = ""
    for attempt in range(1, 4):
        try:
            response = generate_text(
                [{"role": "user", "content": prompt + retry_note}],
                max_tokens=120,
                temperature=min(0.2 + 0.2 * (attempt - 1), 0.6),
            )
            raw_hint = str(parse_json_object(response).get("hint") or "").strip()
            hint = valid_level1_hint(raw_hint, blank_word=blank_word)
            if hint:
                return hint
            # "Streamers are long paper strips"처럼 정의는 맞지만 표제어를
            # 그대로 쓴 경우, 표제어만 쉬운 대명사로 바꿔 뜻풀이는 보존한다.
            pronoun = "They" if blank_word.casefold().endswith("s") else "It"
            without_answer = re.sub(
                rf"\b{re.escape(blank_word)}\b",
                pronoun,
                raw_hint,
                flags=re.IGNORECASE,
            )
            hint = valid_level1_hint(without_answer, blank_word=blank_word)
            if hint and without_answer != raw_hint:
                return hint
            raise ValueError("Meaning hint exposed the answer or used a location cue.")
        except Exception as error:
            last_error = error
            retry_note = (
                "\n\nYour previous hint was invalid. Use a different explanation. "
                "Do not write the answer word, a page/picture instruction, a first-letter "
                "clue, or a fill-in-the-blank sentence. Return exactly one JSON object."
            )
    raise ValueError(
        f"Could not generate a meaning hint for {blank_word!r}."
    ) from last_error


def level1_hint(hint: Any, *, blank_word: str, source_text: str) -> str:
    valid_hint = valid_level1_hint(hint, blank_word=blank_word)
    if valid_hint:
        return valid_hint
    return generate_level1_meaning_hint(blank_word, source_text)


def generate_description_quizzes(lesson: dict[str, Any]) -> list[dict[str, Any]]:
    level = int(lesson.get("level", 1))
    pages = extract_pages(lesson)
    if not pages:
        return []
    count = min(LEVEL_CONFIGS[level].description_scenes, len(pages))
    desc_type = {
        1: DescriptionType.WORD_GUESS,
        2: DescriptionType.SENTENCE,
        3: DescriptionType.REASON,
    }[level]
    level_instruction = {
        1: (
            "Generate only word-guess quizzes. Choose one visible noun or color. "
            "Use a short question. The expected_answer must be exactly one target "
            "word, and that same word must appear first in keywords_for_evaluation. "
            "Do not ask for reasons or abstract feelings. Each hint must explain "
            "the word using very easy English: its meaning, use, color, shape, or "
            "action. Never tell the child to look at a picture, image, scene, "
            "illustration, or page. Never include the answer word in the hint."
        ),
        2: "Generate short-sentence scene-description quizzes.",
        3: "Generate scene-and-reason quizzes whose answer uses because.",
    }[level]
    story_pages = "\n".join(f"Page {number}: {text}" for number, text in pages)
    prompt = DESCRIPTION_QUIZ_PROMPT.format(
        quiz_count=count,
        level=level,
        ar_level={1: "0.1-0.9", 2: "0.9-1.8", 3: "1.8-2.5"}[level],
        level_instruction=level_instruction,
        theme=lesson.get("theme", ""),
        story_pages=story_pages,
    )
    page_text = dict(pages)

    try:
        response = generate_text(
            [{"role": "user", "content": prompt}],
            max_tokens=1400,
            temperature=0.2,
        )
        quizzes = parse_json_object(response).get("quizzes", [])
        results = []
        used_pages: set[int] = set()
        for quiz in quizzes:
            if not isinstance(quiz, dict):
                continue
            page_number = int(quiz.get("page_number", 0))
            if page_number not in page_text or page_number in used_pages:
                continue
            keywords = quiz.get("keywords_for_evaluation") or []
            expected = str(quiz.get("expected_answer") or page_text[page_number])
            blank_word = (
                str(keywords[0]).strip()
                if level == 1 and keywords
                else None
            )
            if level == 1:
                blank_word = blank_word or fallback_blank_word(
                    page_text[page_number]
                )
                if not blank_word:
                    continue
                expected = blank_word
            results.append({
                "scene_number": len(results) + 1,
                "page_number": page_number,
                "text": page_text[page_number],
                "image_path": "",
                "desc_type": desc_type.value,
                "blank_word": blank_word,
                "answer_sentence": expected,
                "guide_hint": (
                    level1_hint(
                        quiz.get("hint_1"),
                        blank_word=blank_word,
                        source_text=page_text[page_number],
                    )
                    if level == 1
                    else quiz.get("hint_1") or expected[:len(expected) // 2]
                ),
            })
            used_pages.add(page_number)
            if len(results) == count:
                return results
    except Exception as error:
        print(f"묘사 문제 생성 실패, 기본 문제 사용: {error}")

    # LLM 응답이 부족하거나 잘못된 경우에도 입력 페이지에서 문제를 만든다.
    return [
        {
            "scene_number": index,
            "page_number": page_number,
            "text": text,
            "image_path": "",
            "desc_type": desc_type.value,
            "blank_word": fallback_blank_word(text) if level == 1 else None,
            "answer_sentence": fallback_blank_word(text) if level == 1 else text,
            "guide_hint": (
                level1_hint(
                    "",
                    blank_word=fallback_blank_word(text),
                    source_text=text,
                )
                if level == 1 and fallback_blank_word(text)
                else text[:len(text) // 2]
            ),
        }
        for index, (page_number, text) in enumerate(pages[:count], 1)
    ]


def generate_file(input_path: Path, output_path: Path | None = None) -> Path:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("accepted_text JSON must contain a top-level list.")
    output = [
        {
            "level": int(lesson.get("level", 1)),
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
    parser = argparse.ArgumentParser(description="Generate description quizzes from accepted text JSON.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    print(f"Description quizzes: {generate_file(args.input, args.output)}")


if __name__ == "__main__":
    main()
