"""최종 accepted text 전체를 검사하고 겹치는 문장을 새 문장으로 교체한다.

Usage:
    python -m scripts.final_duplicate_judge outputs/run/..._accepted_text.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Callable

from ai.llm_client import generate_text
from shared.settings import MODELS


FINAL_DUPLICATE_JUDGE_PROMPT = """
You are the final LLM-as-judge for a children's story curriculum.

Read EVERY sentence in the JSON below and find sentences that duplicate or closely
paraphrase another sentence anywhere in the file. Repeated character names and
necessary story facts are allowed, but a sentence is duplicated when its wording,
action, image, or narrative purpose substantially overlaps an earlier sentence.

For every duplicated sentence after its first occurrence, write one completely new
English fairy-tale sentence. The replacement must:
- fit the same lesson, page position, theme, characters, continuity, and reading level;
- advance the local event instead of repeating an earlier action;
- preserve the original page's narrative purpose where possible;
- not duplicate or closely paraphrase ANY sentence in the supplied file;
- contain only the story sentence, with no explanation.

You MUST copy the "original" field character-for-character from the input JSON for
each duplicate you report. Do not paraphrase, summarize, or fix typos in the
"original" field — copy it exactly, including punctuation and capitalization.

Return ONLY valid JSON in this exact shape:
{{
  "duplicates": [
    {{
      "level": 1,
      "lesson_number": 2,
      "page": "page3",
      "original": "exact original sentence",
      "replacement": "new story sentence",
      "reason": "brief overlap explanation"
    }}
  ]
}}

If there are no overlaps, return {{"duplicates": []}}.
Do not change unique sentences. Use the exact level, lesson_number, page key, and
original sentence from the input so the replacements can be safely applied.

Accepted lessons JSON:
{payload}
""".strip()


def _parse_json_object(text: str) -> dict[str, Any]:
    cleaned = re.sub(r"```(?:json)?|```", "", text).strip()
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise
        value = json.loads(match.group(0))
    if not isinstance(value, dict):
        raise ValueError("Final duplicate judge must return a JSON object.")
    return value


def _page_index(payload: list[dict[str, Any]]) -> dict[tuple[int, int, str], dict[str, str]]:
    index: dict[tuple[int, int, str], dict[str, str]] = {}
    for lesson in payload:
        level = int(lesson.get("level", 0))
        lesson_number = int(lesson.get("lesson_number", 0))
        pages = lesson.get("lesson", [])
        if not isinstance(pages, list):
            raise ValueError("Every lesson field must be a list of page objects.")
        for page in pages:
            if not isinstance(page, dict) or len(page) != 1:
                raise ValueError("Every page must have exactly one pageN field.")
            page_key, sentence = next(iter(page.items()))
            if not isinstance(page_key, str) or not isinstance(sentence, str):
                raise ValueError("Page keys and story sentences must be strings.")
            location = (level, lesson_number, page_key)
            if location in index:
                raise ValueError(f"Duplicate page location in input: {location}")
            index[location] = page
    return index


def _normalize_sentence(sentence: str) -> str:
    """LLM이 따옴표나 문장부호를 보정해도 같은 원문으로 비교한다."""
    return re.sub(r"[^a-z0-9]+", " ", sentence.casefold()).strip()


def _original_matches(actual: str, returned: str) -> bool:
    actual_normalized = _normalize_sentence(actual)
    returned_normalized = _normalize_sentence(returned)
    if not actual_normalized or not returned_normalized:
        return False
    if actual_normalized == returned_normalized:
        return True
    return SequenceMatcher(
        None, actual_normalized, returned_normalized
    ).ratio() >= 0.9


def apply_replacements(
    payload: list[dict[str, Any]],
    verdict: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """중복으로 지목된 문장을 교체한다.

    judge LLM이 위치나 원문을 잘못 인용해도(=흔한 hallucination) 그 항목 하나만
    건너뛰고 나머지 정상적인 교체는 그대로 적용한다. 한 항목의 오류 때문에
    이미 완성된 나머지 lesson 결과 전체를 날리지 않기 위함.
    Returns (updated_payload, skipped_duplicates).
    """
    duplicates = verdict.get("duplicates", [])
    if not isinstance(duplicates, list):
        raise ValueError("Judge response field 'duplicates' must be a list.")

    pages = _page_index(payload)
    normalized_sentences = {
        _normalize_sentence(sentence)
        for page in pages.values()
        for sentence in page.values()
    }
    changed_locations: set[tuple[int, int, str]] = set()
    skipped: list[dict[str, Any]] = []

    for duplicate in duplicates:
        if not isinstance(duplicate, dict):
            skipped.append({"duplicate": duplicate, "reason": "not a JSON object"})
            continue

        location = (
            int(duplicate.get("level", 0)),
            int(duplicate.get("lesson_number", 0)),
            str(duplicate.get("page", "")),
        )
        if location not in pages:
            skipped.append({
                "duplicate": duplicate,
                "reason": f"unknown page location {location}",
            })
            continue
        if location in changed_locations:
            skipped.append({
                "duplicate": duplicate,
                "reason": f"location already changed once {location}",
            })
            continue

        page_key = location[2]
        original = str(duplicate.get("original", "")).strip()
        replacement = str(duplicate.get("replacement", "")).strip()
        actual = pages[location][page_key].strip()

        if not _original_matches(actual, original):
            skipped.append({
                "duplicate": duplicate,
                "reason": (
                    f"judge-quoted original does not match file content at {location}: "
                    f"file has {actual!r}, judge returned {original!r}"
                ),
            })
            continue

        if not replacement or replacement == original:
            skipped.append({
                "duplicate": duplicate,
                "reason": f"no usable replacement sentence for {location}",
            })
            continue

        normalized_replacement = _normalize_sentence(replacement)
        if normalized_replacement in normalized_sentences:
            skipped.append({
                "duplicate": duplicate,
                "reason": f"replacement still duplicates another sentence at {location}",
            })
            continue

        pages[location][page_key] = replacement
        normalized_sentences.add(normalized_replacement)
        changed_locations.add(location)

    return payload, skipped


def judge_and_rewrite_file(
    input_path: Path,
    *,
    model: str | None = None,
    text_generator: Callable[..., str] = generate_text,
) -> dict[str, Any]:
    with input_path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    if not isinstance(payload, list):
        raise ValueError("Accepted text JSON must contain a top-level list.")

    # 입력 형식을 LLM 호출 전에 검증하고, 전체 내용을 한 프롬프트에 담는다.
    _page_index(payload)
    prompt = FINAL_DUPLICATE_JUDGE_PROMPT.format(
        payload=json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    )
    selected_model = model or (
        MODELS.story_judge_models[0]
        if MODELS.story_judge_models
        else MODELS.judge_model
    )
    response = text_generator(
        [{"role": "user", "content": prompt}],
        model=selected_model,
        max_tokens=5000,
        temperature=0.15,
    )
    verdict = _parse_json_object(response)
    updated_payload, skipped = apply_replacements(payload, verdict)

    temporary_path = input_path.with_name(f".{input_path.name}.tmp")
    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(updated_payload, file, ensure_ascii=False, indent=2)
        file.flush()
        os.fsync(file.fileno())
    temporary_path.replace(input_path)

    duplicates = verdict.get("duplicates", [])
    applied_count = len(duplicates) - len(skipped)

    if skipped:
        print(
            f"[final_duplicate_judge] {len(skipped)}/{len(duplicates)}개 항목을 "
            "적용하지 못해 건너뛰었습니다 (judge가 원문을 잘못 인용했거나 "
            "위치가 안 맞음). 나머지 정상 교체는 그대로 반영됐습니다."
        )
        for item in skipped:
            print(f"  - {item['reason']}")

    return {
        "model": selected_model,
        "replacement_count": applied_count,
        "skipped_count": len(skipped),
        "duplicates": duplicates,
        "skipped": skipped,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Use an LLM judge to replace overlapping accepted story sentences."
    )
    parser.add_argument("input", type=Path, help="Path to *_accepted_text.json")
    parser.add_argument("--model", help="Override the configured judge model.")
    args = parser.parse_args()

    report = judge_and_rewrite_file(args.input, model=args.model)
    print(
        f"Final duplicate judge ({report['model']}): "
        f"replaced {report['replacement_count']} sentence(s), "
        f"skipped {report['skipped_count']} unmatched item(s) in {args.input}"
    )


if __name__ == "__main__":
    main()