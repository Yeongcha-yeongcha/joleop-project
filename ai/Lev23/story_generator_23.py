"""Generate Level 2 and Level 3 books from an accepted Level 1 book.

Usage:
	python3 -m ai.Lev23.story_generator_23 \
		--accepted outputs/test15/qwen_judged_lessons_accepted_text.json \
		--plan plans/test1_book_plan.json

The accepted Level 1 lessons provide the story events and order. The plan's
episode_beats are authoritative for the central event of each rewritten lesson.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
from pathlib import Path
from typing import Any

from ai.llm_client import generate_text
from ai.prompts import STORY_GENERATION_PROMPT, STORY_REPAIR_PROMPT
from ai.story_generator import (
	build_avoid_sentences_addendum,
	build_quality_feedback_addendum,
	evaluation_feedback,
	evaluate_story_score,
	extract_story_sentences,
	find_reused_sentences,
	rewrite_reused_story_sentences,
	story_evaluation_passed,
	story_text_from_sentences,
)
from shared.settings import MODELS


LEVELS = (2, 3)
TARGET_LESSONS = 10
MIN_PAGES = 10
MAX_PAGES = 13
TARGET_PAGES = 11
MAX_WORDS = {2: 15, 3: 16}
TARGET_WORDS = {2: 11, 3: 14}
AR_LEVELS = {2: "0.9-1.8", 3: "1.8-2.5"}


def load_json(path: Path) -> Any:
	with path.open(encoding="utf-8") as file:
		return json.load(file)


def load_inputs(accepted_path: Path, plan_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
	accepted = load_json(accepted_path)
	plan = load_json(plan_path)
	if not isinstance(accepted, list):
		raise ValueError("accepted text JSON must contain a top-level list.")
	if not isinstance(plan, dict):
		raise ValueError("book plan must contain a JSON object.")
	if not plan.get("episode_beats"):
		raise ValueError("book plan must define episode_beats.")
	characters = plan.get("recurring_characters")
	if not isinstance(characters, list) or not characters:
		raise ValueError(
			"book plan must define a non-empty recurring_characters list."
		)
	if any(not isinstance(character, str) or not character.strip() for character in characters):
		raise ValueError("every recurring character must be a non-empty string.")
	if len(accepted) != TARGET_LESSONS:
		raise ValueError(
			f"accepted text must contain exactly {TARGET_LESSONS} lessons; "
			f"got {len(accepted)}"
		)
	if len(plan["episode_beats"]) != TARGET_LESSONS:
		raise ValueError(
			f"episode_beats must contain exactly {TARGET_LESSONS} items; "
			f"got {len(plan['episode_beats'])}"
		)
	return accepted, plan


def accepted_sentences(item: dict[str, Any]) -> list[str]:
	lesson = item.get("lesson", [])
	if not isinstance(lesson, list):
		return []
	sentences: list[str] = []
	for page in lesson:
		if isinstance(page, str):
			sentence = page.strip()
		elif isinstance(page, dict):
			value = next(iter(page.values()), "")
			sentence = str(value).strip()
		else:
			sentence = ""
		if sentence:
			sentences.append(sentence)
	return sentences


def accepted_story_title(item: dict[str, Any], plan: dict[str, Any]) -> str:
	"""Return the Level 1 title that must be preserved in every rewrite."""
	title = plan.get("story_title") or item.get("story_title")
	return str(title).strip() if title else ""


def episode_number(item: dict[str, Any], fallback: int) -> int:
	theme = str(item.get("theme", ""))
	try:
		return int(theme.split("Lesson", 1)[1].split(":", 1)[0].strip())
	except (IndexError, ValueError):
		return fallback


def build_rewrite_prompt(
	*,
	base_sentences: list[str],
	story_title: str,
	episode: int,
	total_episodes: int,
	level: int,
	episode_beat: str,
	plan: dict[str, Any],
) -> str:
	page_count = TARGET_PAGES
	reference = story_text_from_sentences(base_sentences)
	if level == 2:
		language_rules = """- Write each story_sentence in 8-11 words whenever possible.
- Fifteen words is an emergency ceiling, not a target.
- Put only one action, feeling, or idea in each sentence.
- Use common concrete words and mostly subject-verb-object grammar.
- Use no more than one connector such as "and", "but", or "because".
- Keep dialogue brief. Avoid stacked details, extra adjectives, and multiple clauses.
- Make the language only a small step harder than Level 1."""
	else:
		language_rules = """- Write each story_sentence in 11-14 words whenever possible.
- Sixteen words is an emergency ceiling, not a target.
- Keep clauses short while using richer dialogue and clear emotional progression."""
	return STORY_GENERATION_PROMPT.format(
		age=plan.get("age", 6),
		level=level,
		theme=episode_beat,
		protagonist=plan.get("protagonist", "the story protagonist"),
		recurring_characters=", ".join(plan["recurring_characters"]),
		episode=episode,
		total_episodes=total_episodes,
		continuity_context=(
			"This lesson is a Level 1 story rewrite. Preserve the reference "
			"lesson's concrete story state and continue the same book."
		),
		episode_transition_instruction=(
			"Rewrite this lesson as the same episode. Keep its central event, "
			"characters, locations, objects, emotions, cause-and-effect, and "
			"ending. Do not add a new conflict or resolve a later episode."
		),
		page_count=page_count,
		min_pages=MIN_PAGES,
		max_pages=MAX_PAGES,
		max_words=MAX_WORDS[level],
	) + f"""

==================================================
[LEVEL {level} REWRITE CONTRACT]
==================================================

Rewrite the reference lesson below for English Level {level}.
- Write between {MIN_PAGES} and {MAX_PAGES} story pages, in the same event order.
- The Level 1 page count does not need to be preserved.
- Keep the same protagonist, recurring characters, locations, objects, emotions,
  problem, actions, consequence, and ending.
- The required central event is: {episode_beat}
- Make that event unmistakable in the story sentences.
- Use AR {AR_LEVELS[level]} difficulty.
{language_rules}
- Do not copy the Level 1 wording. Change language, not story content.
- Keep the exact same story_title: {story_title}
- Keep the story emotionally safe, concrete, visual, and easy to read aloud.

Reference Level 1 lesson:
{reference}
"""


def generate_draft(prompt: str, *, temperature: float = 0.45) -> str:
	"""Generate one rewrite draft using the same failure handling as the base pipeline."""
	try:
		return generate_text(
			[{"role": "user", "content": prompt}],
			model=MODELS.story_model,
			max_tokens=2600,
			temperature=temperature,
		)
	except Exception as error:
		print(f"[Local LLM] 동화 생성 실패: {error}")
		return ""


def repair_invalid_story_json(
	draft: str,
	*,
	base_sentences: list[str],
	episode: int,
	total_episodes: int,
	level: int,
	theme: str,
	plan: dict[str, Any],
) -> list[str]:
	"""Repair an invalid draft once before spending another generation attempt."""
	repair_prompt = STORY_REPAIR_PROMPT.format(
		page_count=TARGET_PAGES,
		min_pages=MIN_PAGES,
		max_pages=MAX_PAGES,
		max_words=MAX_WORDS[level],
		protagonist=plan.get("protagonist", "the story protagonist"),
		level=level,
		age=plan.get("age", 6),
		theme=theme,
		episode=episode,
		total_episodes=total_episodes,
		continuity_context=(
			"Preserve the reference Level 1 lesson's events and order. "
			"Repair formatting without inventing a different episode. "
			"The complete allowed cast is: "
			+ ", ".join(plan["recurring_characters"])
			+ ". Do not add any other character.\n"
			+ story_text_from_sentences(base_sentences)
		),
		draft=draft,
	)
	try:
		repaired = generate_text(
			[{"role": "user", "content": repair_prompt}],
			model=MODELS.story_model,
			max_tokens=2600,
			temperature=0.1,
		)
		return extract_story_sentences(repaired)
	except Exception as error:
		print(f"  JSON 자동 수리 실패: {error}")
		return []


def shorten_overlong_sentences(
	sentences: list[str],
	*,
	level: int,
	theme: str,
) -> list[str] | None:
	"""Shorten over-limit pages one at a time without requiring JSON output."""
	max_words = MAX_WORDS[level]
	target_words = TARGET_WORDS[level]
	overlong_pages = [
		(index, sentence)
		for index, sentence in enumerate(sentences, 1)
		if len(sentence.split()) > max_words
	]
	if not overlong_pages:
		return sentences

	updated = list(sentences)
	for page_number, sentence in overlong_pages:
		replacement = ""
		for repair_attempt in range(1, 3):
			prompt = f"""Shorten this one children's story sentence.

English level: {level}
Story theme: {theme}
Original sentence: {sentence}

Requirements:
- Preserve the same character, action, emotion, object, and meaning.
- Use simple, concrete English.
- Write one complete sentence of about {target_words} words.
- Never exceed {max_words} words.
- End with a period, question mark, or exclamation mark.
- Return ONLY the shortened sentence on one line.
- Do not return JSON, labels, quotation marks, explanations, or markdown.
"""
			try:
				response = generate_text(
					[{"role": "user", "content": prompt}],
					model=MODELS.story_model,
					max_tokens=120,
					temperature=0.1,
				)
			except Exception as error:
				print(
					f"  p{page_number} 문장 축약 재시도 "
					f"{repair_attempt}/2: {error}"
				)
				continue

			lines = [
				line.strip()
				for line in response.replace("```", "").splitlines()
				if line.strip()
			]
			candidate = " ".join(lines[:1]).strip('"“”') if lines else ""
			candidate = re.sub(r"^(?:[-*]|\d+[.)])\s*", "", candidate).strip()
			for prefix in ("Shortened sentence:", "Sentence:", "Answer:"):
				if candidate.lower().startswith(prefix.lower()):
					candidate = candidate[len(prefix):].strip().strip('"“”')
					break
			word_count = len(candidate.split())
			if candidate and word_count <= max_words:
				ending = candidate.rstrip('"”')
				if ending[-1:] not in ".!?":
					candidate = candidate.rstrip() + "."
				replacement = candidate
				break
			failure_reason = (
				f"{word_count}단어로 최대 {max_words}단어 초과"
				if candidate
				else "빈 응답"
			)
			print(
				f"  p{page_number} 문장 축약 재시도 "
				f"{repair_attempt}/2: {failure_reason}"
			)

		if not replacement:
			return None
		updated[page_number - 1] = replacement

	return updated


async def rewrite_lesson(
	*,
	base_item: dict[str, Any],
	plan: dict[str, Any],
	level: int,
	episode: int,
	total_episodes: int,
	previous_sentences: list[str],
) -> dict[str, Any] | None:
	base_sentences = accepted_sentences(base_item)
	if not base_sentences:
		return None
	story_title = accepted_story_title(base_item, plan)
	if not story_title:
		raise ValueError(
			f"Level 1 lesson {episode} does not contain a story_title, and the plan "
			"does not provide a fallback story_title."
		)

	beats = plan["episode_beats"]
	beat = str(beats[episode - 1]) if episode <= len(beats) else str(base_item.get("theme", ""))
	prompt = build_rewrite_prompt(
		base_sentences=base_sentences,
		story_title=story_title,
		episode=episode,
		total_episodes=total_episodes,
		level=level,
		episode_beat=beat,
		plan=plan,
	)
	min_score = int(plan.get("min_score", 70))
	avoid_sentences: list[str] = []
	quality_feedback: list[str] = []
	last_reason = ""
	last_score = 0
	attempt = 0

	print(f"\n{'='*50}")
	print(f"[품질 필터 생성] theme={beat} ep={episode} min_score={min_score}")

	while True:
		attempt += 1
		attempt_prompt = (
			prompt
			+ build_avoid_sentences_addendum(avoid_sentences)
			+ build_quality_feedback_addendum(quality_feedback)
		)
		maximum_temperature = 0.6 if level == 2 else 0.9
		attempt_temperature = min(
			0.45 + 0.15 * (attempt - 1), maximum_temperature
		)
		draft = generate_draft(attempt_prompt, temperature=attempt_temperature)
		if not draft:
			last_reason = "Story generation failed."
			print(f"  초안 재생성 {attempt}회차: 생성 실패")
			continue

		sentences = extract_story_sentences(draft)
		if not sentences:
			print("  → JSON 파싱 실패, 같은 초안 자동 수리 시도")
			sentences = repair_invalid_story_json(
				draft,
				base_sentences=base_sentences,
				episode=episode,
				total_episodes=total_episodes,
				level=level,
				theme=beat,
				plan=plan,
			)
			if not sentences:
				last_reason = (
					"Draft JSON was incomplete or invalid and automatic repair failed; "
					"it was not sent to Qwen or continuity context."
				)
				print(
					f"  초안 재생성 {attempt}회차: "
					"JSON 자동 수리 실패 (Qwen 평가 생략)"
				)
				continue
			print(f"  → JSON 자동 수리 완료 ({len(sentences)}문장 추출)")

		if not MIN_PAGES <= len(sentences) <= MAX_PAGES:
			last_reason = (
				f"expected {MIN_PAGES}-{MAX_PAGES} pages, got {len(sentences)}"
			)
			print(
				f"  초안 재생성 {attempt}회차: "
				f"페이지 수 {len(sentences)}개 "
				f"(허용: {MIN_PAGES}-{MAX_PAGES})"
			)
			continue
		overlong_count = sum(
			len(sentence.split()) > MAX_WORDS[level] for sentence in sentences
		)
		if overlong_count:
			shortened_sentences = shorten_overlong_sentences(
				sentences,
				level=level,
				theme=beat,
			)
			if shortened_sentences is None:
				last_reason = f"a sentence exceeds the Level {level} word limit"
				print(
					f"  초안 재생성 {attempt}회차: "
					f"Level {level} 제한 초과 문장 {overlong_count}개 축약 실패"
				)
				continue
			sentences = shortened_sentences
			print(f"  → 단어 수 초과 문장 {overlong_count}개를 해당 페이지만 축약")

		reused_sentences = find_reused_sentences(
			sentences,
			previous_sentences,
			similarity_threshold=0.94,
		)
		if reused_sentences:
			avoid_sentences.extend(item["sentence"] for item in reused_sentences)
			rewritten_sentences = rewrite_reused_story_sentences(
				sentences,
				reused_sentences,
				episode=episode,
				total_episodes=total_episodes,
				level=level,
				theme=beat,
			)
			remaining_reuse = find_reused_sentences(
				rewritten_sentences,
				previous_sentences,
				similarity_threshold=0.94,
			)
			if remaining_reuse:
				avoid_sentences.extend(item["sentence"] for item in remaining_reuse)
				last_reason = "duplicate rewrite still reused earlier text"
				print(
					f"  초안 재생성 {attempt}회차: "
					f"부분 재작성 후에도 유사 문장 {len(remaining_reuse)}개"
				)
				continue
			sentences = rewritten_sentences
			print(f"  → 중복 문장 {len(reused_sentences)}개를 해당 페이지만 재작성")

		print("  → 초안 저장 완료, Qwen 품질 평가 시작")
		evaluation = evaluate_story_score(
			story_text_from_sentences(sentences),
			episode=episode,
			total_episodes=total_episodes,
			episode_beat=beat,
			previous_sentences=previous_sentences,
			min_score=min_score,
		)
		last_score = int(evaluation.get("total_score", 0))
		passed = bool(evaluation.get("passed")) and story_evaluation_passed(
			evaluation, min_score
		)
		if passed:
			print(f"  ✓ 품질 통과: {last_score}/{min_score}")
			return {
				"level": level,
				"lesson_number": episode,
				"story_title": story_title,
				"theme": beat,
				"lesson": sentences,
				"quality_score": last_score,
				"quality_reason": evaluation.get("reason", ""),
				"evaluation": evaluation,
				"reference_level": 1,
			}
		last_reason = str(evaluation.get("reason", "quality score failed"))
		quality_feedback.extend(evaluation_feedback(evaluation))
		print(f"  품질 재생성 {attempt}회차: {last_score}/{min_score}")


def validate_episode_order(accepted: list[dict[str, Any]], plan: dict[str, Any]) -> None:
	total_episodes = len(plan["episode_beats"])
	accepted_episodes = [episode_number(item, index) for index, item in enumerate(accepted, 1)]
	expected_episodes = list(range(1, total_episodes + 1))
	if accepted_episodes != expected_episodes:
			raise ValueError(
				"accepted lessons must contain every episode in order: "
				f"expected {expected_episodes}, got {accepted_episodes}"
			)


async def generate_level_book(
	accepted: list[dict[str, Any]],
	plan: dict[str, Any],
	level: int,
) -> list[dict[str, Any]]:
	"""Generate all lessons for one level so it can be saved independently."""
	validate_episode_order(accepted, plan)
	# 책 제목은 lesson별 값이 아니다. plan 제목을 우선 사용하고, 구형 plan에
	# 없으면 첫 Level 1 lesson 제목을 책 전체의 고정 제목으로 삼는다.
	fixed_story_title = accepted_story_title(accepted[0], plan)
	if not fixed_story_title:
		raise ValueError("The book does not contain a story_title.")
	plan = {**plan, "story_title": fixed_story_title}
	total_episodes = len(plan["episode_beats"])
	level_output: list[dict[str, Any]] = []
	rewritten_sentences: list[str] = []
	for index, item in enumerate(accepted, 1):
		episode = episode_number(item, index)
		rewritten = await rewrite_lesson(
			base_item=item,
			plan=plan,
			level=level,
			episode=episode,
			total_episodes=total_episodes,
			previous_sentences=rewritten_sentences,
		)
		if rewritten:
			level_output.append(rewritten)
			rewritten_sentences.extend(rewritten["lesson"])
	if len(level_output) != TARGET_LESSONS:
		raise RuntimeError(
			f"Level {level} produced {len(level_output)} lessons; "
			f"required {TARGET_LESSONS}."
		)
	return level_output


def accepted_text_payload(
	lessons: list[dict[str, Any]],
	level: int,
) -> list[dict[str, Any]]:
	"""Convert rewrites to story_generator.py's *_accepted_text.json shape."""
	payload = []
	ordered_lessons = sorted(
		lessons,
		key=lambda item: int(item.get("lesson_number", 0)),
	)
	for fallback, item in enumerate(ordered_lessons, 1):
		lesson_number = int(item.get("lesson_number", fallback))
		payload.append({
			"level": level,
			"lesson_number": lesson_number,
			"story_title": item.get("story_title", ""),
			"theme": item.get("theme", ""),
			"lesson": [
				{f"page{page_number}": sentence}
				for page_number, sentence in enumerate(item.get("lesson", []), 1)
				if sentence
			],
		})
	return payload


def level_output_path(base_path: Path, level: int) -> Path:
	"""Build a distinct accepted-text path without duplicating common suffixes."""
	stem = base_path.stem
	for suffix in ("_accepted_text", "_level23"):
		if stem.endswith(suffix):
			stem = stem[:-len(suffix)]
	return base_path.with_name(f"{stem}_level{level}_accepted_text.json")


def write_json(path: Path, payload: list[dict[str, Any]]) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	temporary = path.with_name(f".{path.name}.tmp")
	with temporary.open("w", encoding="utf-8") as file:
		json.dump(payload, file, ensure_ascii=False, indent=2)
		file.flush()
		os.fsync(file.fileno())
	temporary.replace(path)


def main() -> None:
	parser = argparse.ArgumentParser(description="Generate Level 2 and 3 rewrites from an accepted Level 1 book.")
	parser.add_argument("--accepted", required=True, type=Path)
	parser.add_argument("--plan", required=True, type=Path)
	parser.add_argument(
		"--output",
		type=Path,
		help="Base path used to derive separate Level 2 and Level 3 output names.",
	)
	parser.add_argument("--level2-output", type=Path)
	parser.add_argument("--level3-output", type=Path)
	args = parser.parse_args()

	accepted, plan = load_inputs(args.accepted, args.plan)
	base_output = args.output or args.accepted
	explicit_outputs = {
		2: args.level2_output,
		3: args.level3_output,
	}
	for level in LEVELS:
		lessons = asyncio.run(generate_level_book(accepted, plan, level))
		payload = accepted_text_payload(lessons, level)
		output = explicit_outputs[level] or level_output_path(base_output, level)
		write_json(output, payload)
		print(f"Generated Level {level} accepted text ({len(payload)} lessons): {output}")


if __name__ == "__main__":
	main()
