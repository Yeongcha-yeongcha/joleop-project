"""
Run the story generation pipeline from a saved content plan.

현재 구조
- book1: 각 lesson 10~12 pages
- book2: 각 lesson 12~14 pages
- Level 1 원본 책은 정확히 10 lessons
- curriculum plan에서 Level 1/2/3을 생성할 수 있음
- 첫 번째 level을 기준 스토리로 생성하고, 이후 level은 같은 사건/순서/캐릭터를
  유지하도록 기준 lesson 텍스트를 continuity_context에 넣어 재작성한다.

Usage:
    python -m scripts.generate_lessons --plan plans/content_plan.example.json
    python -m scripts.generate_lessons --plan plans/curriculum_plan.example.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from ai.story_generator import (
    generate_lesson_if_quality_passes,
    generate_tts_for_lesson,
)

DEFAULT_TARGET_LESSONS = 10


def write_checkpoint(
    plan: dict[str, Any],
    result: dict[str, Any],
    *,
    status: str = "running",
) -> None:
    """완료된 lesson 결과를 실행 중에도 안전하게 JSON으로 저장한다."""
    checkpoint_path = plan.get("_checkpoint_path")
    if not checkpoint_path:
        return

    path = Path(checkpoint_path)
    payload = {
        "generation_status": status,
        "updated_at": datetime.now().astimezone().isoformat(),
        **result,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f".{path.name}.tmp")
    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.flush()
        os.fsync(file.fileno())
    temporary_path.replace(path)


def mark_checkpoint_stopped(plan: dict[str, Any], error: BaseException) -> None:
    checkpoint_path = plan.get("_checkpoint_path")
    if not checkpoint_path:
        return

    path = Path(checkpoint_path)
    try:
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        payload = {}

    payload["generation_status"] = (
        "interrupted" if isinstance(error, KeyboardInterrupt) else "failed"
    )
    payload["updated_at"] = datetime.now().astimezone().isoformat()
    payload["error"] = str(error) or error.__class__.__name__
    write_checkpoint(plan, payload, status=payload["generation_status"])


def append_story_draft(plan: dict[str, Any], draft: dict[str, Any]) -> None:
    """Llama 초안을 Qwen 평가 결과와 분리해 생성 즉시 누적 저장한다."""
    draft_path = plan.get("_draft_path")
    if not draft_path:
        return

    path = Path(draft_path)
    try:
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        payload = {"drafts": []}

    payload["generation_status"] = "running"
    payload["updated_at"] = datetime.now().astimezone().isoformat()
    payload.setdefault("drafts", []).append(draft)
    payload["draft_count"] = len(payload["drafts"])

    temporary_path = path.with_name(f".{path.name}.tmp")
    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.flush()
        os.fsync(file.fileno())
    temporary_path.replace(path)


def set_draft_status(plan: dict[str, Any], status: str) -> None:
    draft_path = plan.get("_draft_path")
    if not draft_path:
        return

    path = Path(draft_path)
    try:
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        payload = {"drafts": [], "draft_count": 0}

    payload["generation_status"] = status
    payload["updated_at"] = datetime.now().astimezone().isoformat()
    temporary_path = path.with_name(f".{path.name}.tmp")
    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.flush()
        os.fsync(file.fileno())
    temporary_path.replace(path)


def load_plan(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        plan = json.load(file)

    if "levels" in plan:
        required = ["book_id", "age", "protagonist", "levels"]
        missing = [key for key in required if key not in plan]
        if missing:
            raise ValueError(f"Missing required plan keys: {', '.join(missing)}")

        validate_book_id(plan["book_id"])

        for batch in plan["levels"]:
            validate_batch(batch)

        return plan

    required = ["book_id", "level", "age", "protagonist"]
    missing = [key for key in required if key not in plan]
    if missing:
        raise ValueError(f"Missing required plan keys: {', '.join(missing)}")

    validate_book_id(plan["book_id"])
    validate_batch(plan)
    validate_level_one_book_plan(plan)
    return plan


def validate_book_id(book_id: str) -> None:
    if book_id not in {"book1", "book2"}:
        raise ValueError(
            "book_id must be 'book1' or 'book2'. "
            "story_generator.py currently defines page ranges only for these books."
        )


def validate_batch(batch: dict[str, Any]) -> None:
    if int(batch["level"]) not in [1, 2, 3]:
        raise ValueError("level must be 1, 2, or 3.")

    if not get_episode_beats(batch):
        raise ValueError("themes or episode_beats must include at least one item.")


def validate_level_one_book_plan(plan: dict[str, Any]) -> None:
    """현재 단일 plan은 Level 1 원본 책 한 권만 생성한다."""
    if int(plan["level"]) != 1:
        raise ValueError(
            "This script's single-book plan generates Level 1 only. "
            "Level 2 and Level 3 must later be rewritten from the accepted Level 1 book."
        )
    if get_target_lessons(plan) != DEFAULT_TARGET_LESSONS:
        raise ValueError("A Level 1 book must contain exactly 10 lessons.")
    if len(get_episode_beats(plan)) != DEFAULT_TARGET_LESSONS:
        raise ValueError("A Level 1 book plan must define exactly 10 episode beats.")


def get_episode_beats(plan: dict[str, Any]) -> list[str]:
    return plan.get("episode_beats") or plan.get("themes") or []


def get_target_lessons(plan: dict[str, Any]) -> int:
    return int(plan.get("target_lessons", DEFAULT_TARGET_LESSONS))


def lesson_to_dict(lesson) -> dict[str, Any]:
    """Lesson을 JSON 저장 가능한 dict로 변환한다 (backend 독립)."""
    return {
        "lesson_id": lesson.lesson_id,
        "book_id": lesson.book_id,
        "level": lesson.level,
        "episode": lesson.episode,
        "pages": [
            {
                "page_number": page.page_number,
                "text": page.text,
                "image_prompt": page.image_prompt,
                "image_path": page.image_path,
                "audio_path": page.audio_path,
            }
            for page in lesson.pages
        ],
        "description_scenes": [
            {
                "scene_number": scene.scene_number,
                "page_number": scene.page_number,
                "text": scene.text,
                "image_path": scene.image_path,
                "desc_type": scene.desc_type.value,
                "blank_word": scene.blank_word,
                "answer_sentence": scene.answer_sentence,
                "guide_hint": scene.guide_hint,
            }
            for scene in lesson.description_scenes
        ],
        "roleplay_scenarios": [
            {
                "scenario_id": scenario.scenario_id,
                "topic": scenario.topic.value,
                "level": scenario.level,
                "scene_description": scenario.scene_description,
                "character_name": scenario.character_name,
                "player_goal": scenario.player_goal,
                "model_answer": scenario.model_answer,
                "similar_answers": scenario.similar_answers,
                "hint_sequence": scenario.hint_sequence,
            }
            for scenario in lesson.roleplay_scenarios
        ],
    }


async def run_plan(plan: dict[str, Any]) -> dict[str, Any]:
    if "levels" in plan:
        return await run_curriculum_plan(plan)

    return await run_single_level_plan(plan)


async def run_single_level_plan(plan: dict[str, Any]) -> dict[str, Any]:
    accepted = []
    rejected = []
    accepted_sentences: list[str] = []

    episode_beats = get_episode_beats(plan)
    target_lessons = get_target_lessons(plan)
    next_episode = int(plan.get("start_episode", 1))
    start_episode = next_episode

    max_attempts = max(
        len(episode_beats),
        target_lessons * int(plan.get("max_total_attempts_multiplier", 10)),
    )

    attempt = 0
    episode_avoid_sentences: list[str] = []
    episode_quality_feedback: list[str] = []

    while len(accepted) < target_lessons and attempt < max_attempts:
        theme = episode_beats[(next_episode - start_episode) % len(episode_beats)]
        display_index = len(accepted) + 1
        attempt += 1

        print(
            f"\n[level {plan['level']}] lesson {display_index}/{target_lessons} "
            f"attempt {attempt}/{max_attempts} theme={theme}"
        )

        lesson, quality = await generate_lesson_if_quality_passes(
            book_id=plan["book_id"],
            episode=next_episode,
            level=int(plan["level"]),
            age=int(plan["age"]),
            theme=theme,
            protagonist=plan["protagonist"],
            min_score=int(plan.get("min_score", 75)),
            generate_images=bool(plan.get("generate_images", False)),
            quality_retries=int(plan.get("quality_retries", 5)),
            total_episodes=target_lessons,
            continuity_context=build_continuity_context(
                accepted_sentences,
                next_episode,
                target_lessons,
            ),
            image_output_dir=plan.get("_image_output_dir"),
            on_draft=lambda draft: append_story_draft(plan, draft),
            # 이전에 채택된 문장들을 넘겨서 (1) Qwen judge가 중복을 판단할 근거를
            # 갖게 하고, (2) 생성 단계에서도 값싼 문자열 유사도 체크로 복붙을 거른다.
            previous_sentences=accepted_sentences,
            avoid_sentences=episode_avoid_sentences,
            quality_feedback=episode_quality_feedback,
        )

        if not lesson:
            print(f"  REJECT: {quality.get('score', 0)}/100 - {quality.get('reason', '')}")
            rejected.append(quality)
            write_checkpoint(plan, build_level_result(plan, accepted, rejected, target_lessons))
            continue

        finalized = await finalize_lesson(
            lesson=lesson,
            quality=quality,
            theme=theme,
            plan=plan,
        )

        accepted.append(finalized["result_item"])
        accepted_sentences.extend(finalized["sentences"])
        episode_avoid_sentences.clear()
        episode_quality_feedback.clear()

        print(f"  PASS: {quality['score']}/100 -> {finalized['lesson_id']}")
        next_episode += 1
        write_checkpoint(plan, build_level_result(plan, accepted, rejected, target_lessons))

    return build_level_result(plan, accepted, rejected, target_lessons)


def build_level_result(
    plan: dict[str, Any],
    accepted: list,
    rejected: list,
    target_lessons: int,
) -> dict[str, Any]:
    return {
        "book_id": plan["book_id"],
        "level": int(plan["level"]),
        "book_structure": {
            "source_level": 1,
            "total_lessons": DEFAULT_TARGET_LESSONS,
            "lesson_roles": {
                "1": "beginning",
                "2-9": "development",
                "10": "ending",
            },
            "future_rewrites": [2, 3],
        },
        "target_lessons": target_lessons,
        "min_score": int(plan.get("min_score", 75)),
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "accepted": accepted,
        "rejected": rejected,
    }


async def run_curriculum_plan(plan: dict[str, Any]) -> dict[str, Any]:
    """
    첫 번째 level을 기준 story로 생성하고,
    나머지 level은 기준 story의 사건/캐릭터/순서를 유지한 채
    언어 난이도만 바꾸도록 재생성한다.
    """

    level_batches = sorted(plan["levels"], key=lambda item: int(item["level"]))

    if not level_batches:
        raise ValueError("levels must contain at least one level.")

    target_lessons = int(plan.get("target_lessons", DEFAULT_TARGET_LESSONS))

    base_batch = level_batches[0]
    base_plan = make_batch_plan(
        root_plan=plan,
        batch=base_batch,
        target_lessons=target_lessons,
    )

    print("\n" + "=" * 50)
    print(f"[BASE STORY] Level {base_plan['level']} / {target_lessons} lessons")

    base_result = await run_target_level_plan(base_plan)

    base_lessons = {
        int(item["lesson"]["episode"]): item
        for item in base_result["accepted"]
    }

    level_results = [base_result]
    all_accepted = list(base_result["accepted"])
    all_rejected = list(base_result["rejected"])

    for batch in level_batches[1:]:
        batch_plan = make_batch_plan(
            root_plan=plan,
            batch=batch,
            target_lessons=target_lessons,
        )

        print("\n" + "=" * 50)
        print(f"[LEVEL REWRITE] Level {batch_plan['level']} using base story")

        result = await run_rewrite_level_plan(
            batch_plan,
            base_lessons,
        )

        level_results.append(result)
        all_accepted.extend(result["accepted"])
        all_rejected.extend(result["rejected"])

        write_checkpoint(plan, {
            "book_id": plan["book_id"],
            "target_lessons": target_lessons,
            "base_level": int(base_plan["level"]),
            "accepted_count": len(all_accepted),
            "rejected_count": len(all_rejected),
            "levels": level_results,
            "accepted": all_accepted,
            "rejected": all_rejected,
        })

    return {
        "book_id": plan["book_id"],
        "target_lessons": target_lessons,
        "base_level": int(base_plan["level"]),
        "accepted_count": len(all_accepted),
        "rejected_count": len(all_rejected),
        "levels": level_results,
        "accepted": all_accepted,
        "rejected": all_rejected,
    }


def make_batch_plan(
    *,
    root_plan: dict[str, Any],
    batch: dict[str, Any],
    target_lessons: int,
) -> dict[str, Any]:

    return {
        **batch,
        "book_id": root_plan["book_id"],
        "age": batch.get("age", root_plan["age"]),
        "protagonist": batch.get("protagonist", root_plan["protagonist"]),
        "target_lessons": int(batch.get("target_lessons", target_lessons)),
        "min_score": batch.get("min_score", root_plan.get("min_score", 75)),
        "generate_images": batch.get(
            "generate_images",
            root_plan.get("generate_images", False),
        ),
        "generate_tts": batch.get(
            "generate_tts",
            root_plan.get("generate_tts", False),
        ),
        "quality_retries": batch.get(
            "quality_retries",
            root_plan.get("quality_retries", 5),
        ),
        "max_total_attempts_multiplier": batch.get(
            "max_total_attempts_multiplier",
            root_plan.get("max_total_attempts_multiplier", 10),
        ),
        "_image_output_dir": root_plan.get("_image_output_dir"),
        "_audio_output_dir": root_plan.get("_audio_output_dir"),
        "_checkpoint_path": root_plan.get("_checkpoint_path"),
        "_draft_path": root_plan.get("_draft_path"),
    }


async def run_target_level_plan(plan: dict[str, Any]) -> dict[str, Any]:
    accepted = []
    rejected = []
    accepted_sentences: list[str] = []

    episode_beats = get_episode_beats(plan)
    target_lessons = int(plan.get("target_lessons", DEFAULT_TARGET_LESSONS))
    next_episode = int(plan.get("start_episode", 1))
    start_episode = next_episode

    max_attempts = max(
        len(episode_beats),
        target_lessons * int(plan.get("max_total_attempts_multiplier", 10)),
    )

    attempt = 0
    episode_avoid_sentences: list[str] = []
    episode_quality_feedback: list[str] = []

    while len(accepted) < target_lessons and attempt < max_attempts:
        theme = episode_beats[(next_episode - start_episode) % len(episode_beats)]
        display_index = len(accepted) + 1
        attempt += 1

        print(
            f"\n[level {plan['level']}] lesson {display_index}/{target_lessons} "
            f"attempt {attempt}/{max_attempts} theme={theme}"
        )

        lesson, quality = await generate_lesson_if_quality_passes(
            book_id=plan["book_id"],
            episode=next_episode,
            level=int(plan["level"]),
            age=int(plan["age"]),
            theme=theme,
            protagonist=plan["protagonist"],
            min_score=int(plan.get("min_score", 75)),
            generate_images=bool(plan.get("generate_images", False)),
            quality_retries=int(plan.get("quality_retries", 5)),
            total_episodes=target_lessons,
            continuity_context=build_continuity_context(
                accepted_sentences,
                next_episode,
                target_lessons,
            ),
            image_output_dir=plan.get("_image_output_dir"),
            on_draft=lambda draft: append_story_draft(plan, draft),
            previous_sentences=accepted_sentences,
            avoid_sentences=episode_avoid_sentences,
            quality_feedback=episode_quality_feedback,
        )

        if not lesson:
            print(f"  REJECT: {quality.get('score', 0)}/100 - {quality.get('reason', '')}")
            rejected.append({
                "level": int(plan["level"]),
                "theme": theme,
                **quality,
            })
            write_checkpoint(plan, build_level_result(plan, accepted, rejected, target_lessons))
            continue

        finalized = await finalize_lesson(
            lesson=lesson,
            quality=quality,
            theme=theme,
            plan=plan,
        )

        accepted.append(finalized["result_item"])
        accepted_sentences.extend(finalized["sentences"])
        episode_avoid_sentences.clear()
        episode_quality_feedback.clear()

        print(f"  PASS: {quality['score']}/100 -> {finalized['lesson_id']}")
        next_episode += 1
        write_checkpoint(plan, build_level_result(plan, accepted, rejected, target_lessons))

    return build_level_result(plan, accepted, rejected, target_lessons)


async def run_rewrite_level_plan(
    plan: dict[str, Any],
    base_lessons: dict[int, dict[str, Any]],
) -> dict[str, Any]:

    accepted = []
    rejected = []

    target_lessons = int(plan.get("target_lessons", DEFAULT_TARGET_LESSONS))
    episode_beats = get_episode_beats(plan)

    for episode in range(1, target_lessons + 1):
        base_item = base_lessons.get(episode)

        if not base_item:
            rejected.append({
                "level": int(plan["level"]),
                "episode": episode,
                "accepted": False,
                "score": 0,
                "reason": "Base lesson is missing, so this level cannot rewrite it.",
            })
            write_checkpoint(plan, build_level_result(plan, accepted, rejected, target_lessons))
            continue

        theme = (
            episode_beats[(episode - 1) % len(episode_beats)]
            if episode_beats
            else base_item.get("theme", "story continuation")
        )

        base_lesson = base_item["lesson"]

        base_sentences = [
            page.get("text", "")
            for page in base_lesson.get("pages", [])
            if page.get("text")
        ]

        rewrite_context = build_level_rewrite_context(
            base_sentences=base_sentences,
            episode=episode,
            total_episodes=target_lessons,
            target_level=int(plan["level"]),
        )

        print(
            f"\n[level {plan['level']}] rewrite lesson "
            f"{episode}/{target_lessons} theme={theme}"
        )

        # 재작성(rewrite) 단계는 앞선 base 문장을 "그대로 재사용해도 되는"
        # 유일한 경우다 (난이도만 바꿔 같은 사건을 다시 서술). 따라서 여기서는
        # previous_sentences 중복 검사를 걸지 않는다 — 걸면 의도된 재사용까지
        # 오탐(false positive)으로 막아버린다.
        lesson, quality = await generate_lesson_if_quality_passes(
            book_id=plan["book_id"],
            episode=episode,
            level=int(plan["level"]),
            age=int(plan["age"]),
            theme=theme,
            protagonist=plan["protagonist"],
            min_score=int(plan.get("min_score", 75)),
            generate_images=bool(plan.get("generate_images", False)),
            quality_retries=int(plan.get("quality_retries", 5)),
            total_episodes=target_lessons,
            continuity_context=rewrite_context,
            image_output_dir=plan.get("_image_output_dir"),
            on_draft=lambda draft: append_story_draft(plan, draft),
        )

        if not lesson:
            print(f"  REJECT: {quality.get('score', 0)}/100 - {quality.get('reason', '')}")
            rejected.append({
                "level": int(plan["level"]),
                "episode": episode,
                "theme": theme,
                **quality,
            })
            write_checkpoint(plan, build_level_result(plan, accepted, rejected, target_lessons))
            continue

        finalized = await finalize_lesson(
            lesson=lesson,
            quality=quality,
            theme=theme,
            plan=plan,
            reference_level=int(
                base_item.get(
                    "level",
                    base_lesson.get("level", 1),
                )
            ),
            reference_lesson_id=base_lesson.get("lesson_id"),
        )

        accepted.append(finalized["result_item"])
        write_checkpoint(plan, build_level_result(plan, accepted, rejected, target_lessons))

        print(f"  PASS rewrite: {quality['score']}/100 -> {finalized['lesson_id']}")

    return build_level_result(plan, accepted, rejected, target_lessons)


def build_level_rewrite_context(
    *,
    base_sentences: list[str],
    episode: int,
    total_episodes: int,
    target_level: int,
) -> str:

    numbered = "\n".join(
        f"{idx + 1}. {sentence}"
        for idx, sentence in enumerate(base_sentences)
    )

    return f"""
This is episode {episode} of {total_episodes}.

IMPORTANT:
Rewrite the reference lesson below for English Level {target_level}.

The story CONTENT must remain the same.

Do NOT change:
- main characters
- side characters
- events
- event order
- locations
- important objects
- emotions
- cause-and-effect relationships
- problem
- resolution
- ending
- lesson/theme

Only change:
- vocabulary difficulty
- grammar difficulty
- sentence structure
- connective expressions
- amount of linguistic detail appropriate for Level {target_level}

The rewritten lesson must still satisfy the page range required for this book.

Reference lesson:
{numbered}
""".strip()


async def finalize_lesson(
    *,
    lesson,
    quality: dict[str, Any],
    theme: str,
    plan: dict[str, Any],
    reference_level: Optional[int] = None,
    reference_lesson_id: Optional[str] = None,
) -> dict[str, Any]:

    if plan.get("generate_tts", False):
        lesson = generate_tts_for_lesson(
            lesson,
            plan.get("_audio_output_dir", "audio"),
        )

    lesson_data = lesson_to_dict(lesson)
    lesson_data["theme"] = theme
    lesson_data["quality_score"] = quality["score"]
    lesson_data["quality_reason"] = quality.get("reason", "")

    if reference_level is not None:
        lesson_data["reference_level"] = reference_level

    if reference_lesson_id:
        lesson_data["reference_lesson_id"] = reference_lesson_id

    result_item = {
        "level": int(plan["level"]),
        "theme": theme,
        "episode_role": episode_role(
            int(lesson_data["episode"]),
            int(plan.get("target_lessons", DEFAULT_TARGET_LESSONS)),
        ),
        "score": quality["score"],
        "reason": quality.get("reason", ""),
        "lesson": lesson_data,
        "evaluation": quality.get("evaluation", {}),
    }

    return {
        "result_item": result_item,
        "sentences": [page.text for page in lesson.pages],
        "lesson_id": lesson.lesson_id,
    }


def build_continuity_context(
    previous_sentences: list[str],
    episode: int,
    total_episodes: int,
) -> str:

    role = episode_role(episode, total_episodes)

    if not previous_sentences:
        return (
            f"This is Lesson {episode} of exactly {total_episodes} in one continuous Level 1 book. "
            "This is the beginning of the book. Introduce the protagonist, recurring setting, "
            "main goal, and first child-safe problem. Start the longer story but do not solve "
            "the main goal yet. Later Level 2 and Level 3 versions will preserve these exact "
            "characters, events, event order, and ending."
        )

    anchors = previous_sentences[:4]
    recent = previous_sentences[-8:]
    context_sentences = anchors + [s for s in recent if s not in anchors]
    previous_text = "\n".join(f"- {sentence}" for sentence in context_sentences)

    progression = (
        "Continue the middle development. Advance the same main goal with a new connected event. "
        "Do not resolve the whole book yet, and leave a clear reason for the next lesson."
        if episode < total_episodes
        else
        "This is the final lesson. Resolve the main goal and open story threads established "
        "since Lesson 1, then give the same characters a warm, complete ending."
    )

    return (
        f"This is Lesson {episode} of exactly {total_episodes} in one continuous Level 1 book. "
        f"Its role is {role}. {progression} "
        "Keep every recurring character, setting, important object, goal, and cause-and-effect "
        "relationship consistent. Do not restart the story or introduce a replacement plot. "
        "Later Level 2 and Level 3 rewrites must be able to preserve these exact events.\n"
        "The lines below are PAST events, listed only so you remember who the characters are "
        "and what already happened. They are reference material, not text to reuse. Do NOT "
        "copy, quote, or closely paraphrase any of these lines in this lesson — every "
        "story_sentence you write now must be new text that dramatizes THIS lesson's own "
        "Current episode beat, a distinct event that has not already happened in the lines below.\n"
        "Story anchors and most recent accepted events (reference only, do not copy):\n"
        f"{previous_text}"
    )


def episode_role(episode: int, total_episodes: int) -> str:
    if episode <= 1:
        return "beginning"
    if episode >= total_episodes:
        return "ending"
    return "development"


def write_output(result: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(result, file, ensure_ascii=False, indent=2)


def write_accepted_text_output(result: dict[str, Any], output_path: Path) -> Path:
    """accepted lesson에서 level, lesson 번호, theme, 본문 문장을 저장한다."""
    accepted_text_path = output_path.with_name(
        f"{output_path.stem}_accepted_text.json"
    )
    accepted_text_path.parent.mkdir(parents=True, exist_ok=True)

    accepted_lessons = []
    for item in result.get("accepted", []):
        lesson = item.get("lesson", {})
        level = int(
            item.get("level")
            or lesson.get("level")
            or result.get("level")
            or 0
        )
        lesson_number = int(lesson.get("episode", 0))
        accepted_lessons.append((
            level,
            lesson_number,
            {
                "level": level,
                "lesson_number": lesson_number,
                "theme": item.get("theme") or lesson.get("theme", ""),
                "lesson": [
                    {
                        f"page{page.get('page_number', 0)}": page.get("text", "")
                    }
                    for page in sorted(
                        lesson.get("pages", []),
                        key=lambda page: page.get("page_number", 0),
                    )
                    if page.get("text")
                ],
            },
        ))

    accepted_lessons.sort(key=lambda entry: (entry[0], entry[1]))
    payload = [entry[2] for entry in accepted_lessons]

    temporary_path = accepted_text_path.with_name(
        f".{accepted_text_path.name}.tmp"
    )
    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.flush()
        os.fsync(file.fileno())
    temporary_path.replace(accepted_text_path)
    return accepted_text_path


def write_story_text_output(result: dict[str, Any], output_path: Path) -> None:
    story_path = output_path.with_name(f"{output_path.stem}_stories.md")
    story_path.parent.mkdir(parents=True, exist_ok=True)

    accepted = result.get("accepted", [])

    lines = [
        "# Generated Story Texts",
        "",
        f"- Book ID: {result.get('book_id', '')}",
        f"- Accepted lessons: {result.get('accepted_count', len(accepted))}",
        f"- Rejected attempts: {result.get('rejected_count', 0)}",
        "",
    ]

    grouped: dict[int, list[dict[str, Any]]] = {}

    for item in accepted:
        lesson = item.get("lesson", {})
        level = int(
            item.get("level")
            or lesson.get("level")
            or result.get("level")
            or 0
        )
        grouped.setdefault(level, []).append(item)

    total_sentences = 0

    for level in sorted(grouped):
        lessons = sorted(
            grouped[level],
            key=lambda item: item.get("lesson", {}).get("episode", 0),
        )

        level_sentence_count = sum(
            len(item.get("lesson", {}).get("pages", []))
            for item in lessons
        )

        total_sentences += level_sentence_count

        lines.extend([
            f"## Level {level}",
            "",
            "All levels are intended to describe the same book content with different language difficulty.",
            "",
            f"- Lessons: {len(lessons)}",
            f"- Sentences/pages: {level_sentence_count}",
            "",
        ])

        for item in lessons:
            lesson = item.get("lesson", {})
            episode = lesson.get("episode", "")
            theme = item.get("theme") or lesson.get("theme", "")
            score = item.get("score", lesson.get("quality_score", ""))
            lesson_id = lesson.get("lesson_id", "")

            lines.extend([
                f"### Level {level} - Lesson {episode}",
                "",
                f"- Lesson ID: {lesson_id}",
                f"- Episode beat: {theme}",
                f"- Score: {score}",
                "",
            ])

            for page in lesson.get("pages", []):
                page_number = page.get("page_number", "")
                text = page.get("text", "")
                lines.append(f"{page_number}. {text}")

            lines.append("")

    lines.extend([
        "## Summary",
        "",
        f"- Total accepted lessons: {len(accepted)}",
        f"- Total accepted sentences/pages: {total_sentences}",
        "",
    ])

    with story_path.open("w", encoding="utf-8") as file:
        file.write("\n".join(lines))


async def async_main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate judged story lessons from a content plan."
    )

    parser.add_argument(
        "--plan",
        default="plans/content_plan.example.json",
        help="Path to a JSON content plan.",
    )

    parser.add_argument(
        "--output",
        help="Override output JSON path.",
    )

    parser.add_argument(
        "--run-name",
        help="Name of this run's folder. Must not already exist.",
    )

    parser.add_argument(
        "--output-root",
        default="outputs",
        help="Parent directory for run folders.",
    )

    parser.add_argument(
        "--no-story-text",
        action="store_true",
        help="Do not write the readable Markdown story text file.",
    )

    args = parser.parse_args()

    plan_path = Path(args.plan)
    plan = load_plan(plan_path)

    plan.setdefault("target_lessons", DEFAULT_TARGET_LESSONS)

    run_name = (
        args.run_name
        or plan.get("run_name")
        or datetime.now().strftime("run_%Y%m%d_%H%M%S_%f")
    )

    if Path(run_name).name != run_name or run_name in {"", ".", ".."}:
        parser.error("--run-name must be a single folder name, not a path.")

    run_dir = Path(args.output_root) / run_name

    try:
        run_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        parser.error(
            f"Run folder already exists: {run_dir}. Choose another --run-name."
        )

    image_dir = run_dir / "images"
    audio_dir = run_dir / "audio"

    image_dir.mkdir()
    audio_dir.mkdir()

    plan["_image_output_dir"] = str(image_dir)
    plan["_audio_output_dir"] = str(audio_dir)

    requested_output = (
        args.output
        or plan.get("output_path", "generated_lessons.json")
    )

    output_path = run_dir / Path(requested_output).name
    plan["_checkpoint_path"] = str(output_path)
    plan["_draft_path"] = str(run_dir / "llama_story_drafts.json")

    write_checkpoint(
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
        result = await run_plan(plan)
    except BaseException as error:
        mark_checkpoint_stopped(plan, error)
        set_draft_status(
            plan,
            "interrupted" if isinstance(error, KeyboardInterrupt) else "failed",
        )
        raise

    write_checkpoint(plan, result, status="completed")
    set_draft_status(plan, "completed")
    accepted_text_path = write_accepted_text_output(result, output_path)

    if not args.no_story_text:
        write_story_text_output(result, output_path)

    print("\nDone.")
    print(f"Accepted: {result['accepted_count']}")
    print(f"Rejected: {result['rejected_count']}")
    print(f"Output: {output_path}")
    print(f"Accepted text JSON: {accepted_text_path}")

    if not args.no_story_text:
        print(
            f"Story text: "
            f"{output_path.with_name(f'{output_path.stem}_stories.md')}"
        )


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
