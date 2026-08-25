"""
콘텐츠 제작 파이프라인
① 로컬 Llama로 동화 생성
② Qwen judge로 품질 점수 평가
③ 후처리 검사 (문장 수, 어휘, 반복, 문법)
④ 이미지 프롬프트/이미지 + 롤플레잉 시나리오 생성
"""

import re
import json
import sys
from difflib import SequenceMatcher
from pathlib import Path
from typing import Callable, Optional

# `python ai/story_generator.py`로 직접 실행해도 프로젝트 루트의
# shared/, scripts/ 패키지를 찾을 수 있게 한다.
if __package__ in {None, ""}:
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from shared.settings import MODELS, LEVEL_CONFIGS, IMAGE_STYLE_GUIDE
from ai.image_generator import attach_planned_image_paths, generate_story_images
from ai.llm_client import generate_text
from ai.prompts import (
    DESCRIPTION_QUIZ_PROMPT,
    DUPLICATE_SENTENCE_REWRITE_PROMPT,
    ROLEPLAY_MISSION_PROMPT,
    STORY_GENERATION_PROMPT,
    STORY_JUDGE_PROMPT,
    STORY_SCORE_PROMPT,
)

STORY_SCORE_CRITERIA = [
    "story_structure_completeness",
    "emotional_progression_clarity",
    "character_growth",
    "child_emotional_relatability",
    "emotional_warmth",
    "readability",
    "sentence_simplicity",
    "repetition_effectiveness",
    "read_aloud_quality",
    "dialogue_naturalness",
    "visual_scene_clarity",
    "illustration_friendliness",
    "description_quiz_compatibility",
    "roleplay_compatibility",
    "emotional_safety",
    "creativity",
    "memorability",
    "theme_consistency",
    "educational_suitability",
    "award_level_literary_feeling",
]
from shared.models import (
    StoryPage, DescriptionScene, RoleplayScenario,
    DescriptionType, RoleplayTopic, Lesson
)

# 동화 초안 텍스트 생성
def call_local_story_model(prompt: str, *, temperature: float = 0.45) -> str:
    """로컬 Llama 모델로 동화 초안 생성."""
    try:
        return generate_text(
            [{"role": "user", "content": prompt}],
            model=MODELS.story_model,
            # 10~14 pages 각각에 문장/번역/이미지 설명이 포함되므로
            # 900 tokens에서는 JSON 끝부분이 자주 잘린다.
            max_tokens=2600,
            temperature=temperature,
        )
    except Exception as e:
        print(f"[Local LLM] 동화 생성 실패: {e}")
        return ""


# ─── 동화 생성 프롬프트 ───────────────────────────────────────

def build_episode_transition_instruction(episode: int, total_episodes: int) -> str:
    """레슨 위치에 맞춰 이전 사건을 반복하지 않고 다음 사건으로 이어지게 한다."""
    if episode <= 1:
        return (
            "This is the opening lesson. Introduce the protagonist and the first "
            "problem without referring to events that have not happened yet."
        )

    if episode == total_episodes:
        return (
            "This is the FINAL lesson. Begin from the concrete result left by the "
            "previous accepted lesson and move directly into the final episode beat. "
            "Do not recap earlier lessons page by page. Resolve the book-wide goal "
            "here, show the characters reacting to that resolution, and end warmly. "
            "You may mention established objects, promises, and earlier events, but "
            "every sentence must use new wording and describe the present ending, "
            "not replay an old scene."
        )

    if episode == total_episodes - 1:
        return (
            "This is the PENULTIMATE lesson. Start from the exact story state left "
            "by the previous accepted lesson. Do not repeat that lesson's problem or "
            "solution. Spend this lesson on the new Current episode beat and make its "
            "main action visibly happen on the page. End with a concrete new state "
            "that makes the final lesson possible, but do NOT declare the book-wide "
            "goal complete or celebrate the final success yet."
        )

    return (
        "This is a middle lesson. Continue directly from the previous accepted "
        "lesson, do not replay its scenes, and use the Current episode beat as the "
        "new action that moves the same plot forward."
    )


def build_story_prompt(
    book_id: str,
    age: int,
    level: int,
    theme: str,
    protagonist: str,
    *,
    episode: int = 1,
    total_episodes: int = 1,
    continuity_context: str = "This is episode 1. Start the longer story gently.",
) -> str:
    max_words = max_words_for_level(level)
    min_pages, max_pages = page_range_for_book(book_id)
    page_count = (min_pages + max_pages) // 2
    return STORY_GENERATION_PROMPT.format(
        age=age,
        level=level,
        theme=theme,
        protagonist=protagonist,
        episode=episode,
        total_episodes=total_episodes,
        continuity_context=continuity_context,
        episode_transition_instruction=build_episode_transition_instruction(
            episode, total_episodes
        ),
        page_count=page_count,
        min_pages=min_pages,
        max_pages=max_pages,
        max_words=max_words,
    )


def build_avoid_sentences_addendum(avoid_sentences: list[str]) -> str:
    """이전 시도에서 이미 중복으로 거부된 문장을 다음 시도 프롬프트에 덧붙인다."""
    if not avoid_sentences:
        return ""
    unique_avoid = list(dict.fromkeys(avoid_sentences))[-10:]
    avoid_block = "\n".join(f"- {sentence}" for sentence in unique_avoid)
    return (
        "\n\n==================================================\n"
        "[AVOID THESE ALREADY-REJECTED LINES]\n"
        "==================================================\n"
        "An earlier draft for THIS SAME lesson reused the lines below almost word "
        "for word from an earlier lesson in the book. Do not write these sentences "
        "again, and do not write a close paraphrase (same subject + same verb + "
        "same object) of any of them. For the part of the story that needed one of "
        "these lines, invent a genuinely different concrete action or line of "
        "dialogue instead.\n"
        f"{avoid_block}"
    )


def build_quality_feedback_addendum(feedback_items: list[str]) -> str:
    """이전 Judge의 개선 의견을 다음 초안 생성에 전달한다."""
    cleaned = [item.strip() for item in feedback_items if item and item.strip()]
    if not cleaned:
        return ""
    feedback_block = "\n".join(f"- {item}" for item in cleaned[-8:])
    return (
        "\n\n==================================================\n"
        "[FIX THESE JUDGE ISSUES FROM EARLIER DRAFTS]\n"
        "==================================================\n"
        "Regenerate the lesson with new wording and correct every issue below. "
        "Do not merely explain the fixes; apply them in the story pages.\n"
        f"{feedback_block}"
    )


def evaluation_feedback(evaluation: dict) -> list[str]:
    """다양한 Judge 응답 형식에서 재생성에 쓸 짧은 피드백을 추출한다."""
    feedback: list[str] = []
    reason = evaluation.get("reason")
    if isinstance(reason, str) and reason.strip():
        feedback.append(reason.strip())
    analysis = evaluation.get("analysis")
    if isinstance(analysis, dict):
        areas = analysis.get("areas_for_improvement", [])
        if isinstance(areas, list):
            feedback.extend(str(item).strip() for item in areas if str(item).strip())
    scores = evaluation.get("category_scores") or {}
    weak = [
        f"Improve {key} (judge score: {scores.get(key)})."
        for key in STORY_SCORE_CRITERIA
        if key in scores and int(scores[key]) < 3
    ]
    critical = [
        "emotional_safety",
        "readability",
        "visual_scene_clarity",
        "roleplay_compatibility",
    ]
    weak.extend(
        f"Raise critical criterion {key} to at least 4 "
        f"(judge score: {scores.get(key)})."
        for key in critical
        if key in scores and int(scores[key]) == 3
    )
    feedback.extend(weak)
    return feedback


def max_words_for_level(level: int) -> int:
    return {1: 10, 2: 14, 3: 16}[level]


def page_range_for_book(book_id: str) -> tuple[int, int]:
    """책별 허용 페이지(=문장) 수 범위."""
    ranges = {
        "book1": (10, 12),
        "book2": (12, 14),
    }
    if book_id not in ranges:
        raise ValueError(f"지원하지 않는 book_id: {book_id}")
    return ranges[book_id]


def extract_story_sentences(text: str) -> list[str]:
    json_sentences = extract_story_sentences_from_json(text)
    if json_sentences:
        return json_sentences

    story_sentence_patterns = [
        r"(?:-\s*)?Story sentence\s*:\s*[\"“”']?(.*?)[\"“”']?\s*$",
        r"(?:-\s*)?Story Sentence\s*:\s*[\"“”']?(.*?)[\"“”']?\s*$",
        r"(?:-\s*)?Sentence\s*:\s*[\"“”']?(.*?)[\"“”']?\s*$",
        r"(?:-\s*)?Text\s*:\s*[\"“”']?(.*?)[\"“”']?\s*$",
    ]
    sentences = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        for pattern in story_sentence_patterns:
            match = re.search(pattern, line, flags=re.IGNORECASE)
            if match:
                sentence = _clean_story_sentence(match.group(1))
                if sentence:
                    sentences.append(sentence)
                break

    if sentences:
        return sentences

    numbered_sentences = []
    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not re.match(r"^\d+[\.)]\s*", line):
            continue
        sentence = _clean_story_sentence(re.sub(r"^\d+[\.)]\s*", "", line))
        if looks_like_story_sentence(sentence):
            numbered_sentences.append(sentence)
    return numbered_sentences


def extract_story_sentences_from_json(text: str) -> list[str]:
    try:
        data = parse_json_object(text)
    except Exception:
        return []

    pages = data.get("pages", [])
    if not isinstance(pages, list):
        return []

    sentences = []
    for page in pages:
        if not isinstance(page, dict):
            continue
        sentence = (
            page.get("story_sentence")
            or page.get("Story sentence")
            or page.get("sentence")
            or page.get("text")
        )
        if sentence:
            sentences.append(_clean_story_sentence(str(sentence)))
    return [sentence for sentence in sentences if sentence]


def looks_like_story_sentence(sentence: str) -> bool:
    lowered = sentence.lower()
    metadata_markers = [
        "story title",
        "ar level",
        "main theme",
        "emotional goal",
        "story structure",
        "page number",
        "korean translation",
        "illustration idea",
    ]
    if any(marker in lowered for marker in metadata_markers):
        return False
    if ":" in sentence and len(sentence.split()) < 8:
        return False
    return bool(re.search(r"[.!?\"”']$", sentence))


def _clean_story_sentence(sentence: str) -> str:
    sentence = sentence.strip().strip("\"'“”")
    sentence = re.sub(r"\s+", " ", sentence)
    return sentence


def story_text_from_sentences(sentences: list[str]) -> str:
    return "\n".join(f"{i + 1}. {sentence}" for i, sentence in enumerate(sentences))


def find_reused_sentences(
    sentences: list[str],
    previous_sentences: list[str],
    *,
    similarity_threshold: float = 0.93,
) -> list[dict]:
    """Return likely copies/near-copies of sentences from accepted lessons.

    Level 1 books are intentionally repetitive (Geisel-style short, predictable
    sentence patterns), so some cross-lesson vocabulary/structure overlap is
    expected, not a bug. The threshold is set high enough to still catch
    verbatim or near-verbatim reuse, while tolerating the book's normal
    repetitive style. Short sentences are skipped entirely since a 5-6 word
    Level 1 sentence has very few ways to be phrased at all.
    """
    reused = []
    for sentence in sentences:
        normalized = " ".join(re.findall(r"[a-z0-9']+", sentence.lower()))
        if len(normalized.split()) < 5:
            continue
        for previous in previous_sentences:
            normalized_previous = " ".join(
                re.findall(r"[a-z0-9']+", previous.lower())
            )
            if not normalized_previous:
                continue
            similarity = SequenceMatcher(
                None, normalized, normalized_previous
            ).ratio()
            if similarity >= similarity_threshold:
                reused.append({
                    "sentence": sentence,
                    "previous_sentence": previous,
                    "similarity": round(similarity, 3),
                })
                break
    return reused


def rewrite_reused_story_sentences(
    sentences: list[str],
    reused_sentences: list[dict],
    *,
    episode: int,
    total_episodes: int,
    level: int,
    theme: str,
) -> list[str]:
    """중복으로 판정된 페이지만 LLM으로 다시 쓰고 나머지는 보존한다."""
    duplicate_pages = []
    target_pages: set[int] = set()
    for reused in reused_sentences:
        sentence = reused["sentence"]
        try:
            page_number = sentences.index(sentence) + 1
        except ValueError:
            continue
        if page_number in target_pages:
            continue
        target_pages.add(page_number)
        duplicate_pages.append({
            "page_number": page_number,
            "current_sentence": sentence,
            "overlaps_with": reused["previous_sentence"],
        })

    if not duplicate_pages:
        return sentences

    prompt = DUPLICATE_SENTENCE_REWRITE_PROMPT.format(
        episode=episode,
        total_episodes=total_episodes,
        level=level,
        theme=theme,
        max_words=max_words_for_level(level),
        current_lesson=story_text_from_sentences(sentences),
        duplicate_pages=json.dumps(duplicate_pages, ensure_ascii=False, indent=2),
    )
    try:
        response = generate_text(
            [{"role": "user", "content": prompt}],
            model=MODELS.story_model,
            max_tokens=1000,
            temperature=0.75,
        )
        data = parse_json_object(response)
        replacements = data.get("replacements", [])
        if not isinstance(replacements, list):
            return sentences

        updated = list(sentences)
        replaced_pages: set[int] = set()
        for item in replacements:
            if not isinstance(item, dict):
                continue
            page_number = int(item.get("page_number", 0))
            replacement = _clean_story_sentence(
                str(item.get("story_sentence", ""))
            )
            if page_number not in target_pages or not replacement:
                continue
            if len(replacement.split()) > max_words_for_level(level):
                continue
            if not re.search(r"[.!?]$", replacement):
                continue
            updated[page_number - 1] = replacement
            replaced_pages.add(page_number)

        return updated if replaced_pages == target_pages else sentences
    except Exception as error:
        print(f"  중복 페이지 부분 재작성 실패: {error}")
        return sentences


def parse_json_object(text: str) -> dict:
    text = re.sub(r"```json|```", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def complete_missing_judge_scores(
    *,
    judge_model: str,
    story_context: str,
    partial_result: dict,
) -> dict:
    """Qwen이 20개 점수 중 일부를 생략했을 때 빠진 점수만 짧게 재요청한다."""
    scores = partial_result.get("category_scores")
    if not isinstance(scores, dict):
        scores = {}

    merged_scores = {
        key: int(scores[key])
        for key in STORY_SCORE_CRITERIA
        if key in scores and str(scores[key]).isdigit() and 1 <= int(scores[key]) <= 5
    }
    missing = [key for key in STORY_SCORE_CRITERIA if key not in merged_scores]
    if not missing:
        completed = dict(partial_result)
        completed["category_scores"] = merged_scores
        completed["total_score"] = sum(merged_scores.values())
        return completed

    missing_schema = ",\n".join(f'    "{key}": <1-5>' for key in missing)
    repair_prompt = f"""You are completing an incomplete scoring JSON for a children's story.

Score ONLY the missing criteria listed below. Use integers 1 through 5.
Return every requested key exactly once. Do not return explanations, markdown,
or any keys other than category_scores.

Missing criteria:
{chr(10).join('- ' + key for key in missing)}

Return ONLY this JSON shape:
{{
  "category_scores": {{
{missing_schema}
  }}
}}

Scoring reminders:
- 5 = excellent for the target child/English-learning level
- 4 = strong and production-ready
- 3 = acceptable
- 2 = weak
- 1 = unacceptable
- roleplay_compatibility considers whether a child can naturally help, ask,
  encourage, comfort, or choose in the scene.
- emotional_safety considers child-safe, non-overwhelming content.
- theme_consistency checks whether the required current episode beat is the
  unmistakable main event.

Story and lesson context:
{story_context}
"""
    repair_text = generate_text(
        [{"role": "user", "content": repair_prompt}],
        model=judge_model,
        max_tokens=900,
        temperature=0.0,
    )
    repair_result = parse_json_object(repair_text)
    repair_scores = repair_result.get("category_scores") or {}
    for key in missing:
        if key in repair_scores:
            value = int(repair_scores[key])
            if 1 <= value <= 5:
                merged_scores[key] = value

    completed = dict(partial_result)
    completed["category_scores"] = merged_scores
    if len(merged_scores) == len(STORY_SCORE_CRITERIA):
        completed["total_score"] = sum(merged_scores.values())
    return completed


def evaluate_story_score(
    story_text: str,
    *,
    episode: int = 1,
    total_episodes: int = 1,
    episode_beat: str = "",
    previous_sentences: Optional[list[str]] = None,
    min_score: int =70,
    judge_retries: int = 3,
) -> dict:
    serialized_context = (
        f"This is Lesson {episode} of {total_episodes} in one continuous book. "
        f"Required central event for this lesson: {episode_beat or 'not supplied'}. "
        "Judge this text as its assigned part of the longer story. "
        "A middle lesson should advance the plot without ending the whole book; "
        "only the final lesson must resolve the overall story.\n\n"
    )
    if previous_sentences:
        # 전체 8~9개 레슨 문장을 Judge prompt에 다시 넣으면 후반 레슨에서
        # Qwen 7B가 긴 입력 때문에 출력 스키마의 뒤쪽 필드를 자주 생략한다.
        # 전체 중복 검사는 evaluate 이전의 find_reused_sentences()가 담당하고,
        # Judge에는 직전 흐름을 이해할 정도의 최근 문장만 전달한다.
        recent_references = previous_sentences[-12:]
        references = story_text_from_sentences(recent_references)
        serialized_context += (
            "Recent reference lines from the previous story state. Use these only "
            "to judge continuity; deterministic duplicate checking was already done "
            "before this evaluation:\n"
            f"{references}\n\n"
        )
    story_context = serialized_context + story_text
    prompt = STORY_SCORE_PROMPT.format(
        story=story_context,
        min_score=min_score,
    )
    evaluations = []

    for judge_model in MODELS.story_judge_models:
        for judge_attempt in range(1, judge_retries + 1):
            try:
                retry_instruction = (
                    "\n\nYour previous response was incomplete. Return all 20 exact "
                    "category_scores fields from the requested schema."
                    if judge_attempt > 1
                    else ""
                )
                text = generate_text(
                    [{"role": "user", "content": prompt + retry_instruction}],
                    model=judge_model,
                    max_tokens=1800,
                    temperature=0.1,
                )
                result = parse_json_object(text)
                scores = result.get("category_scores")
                missing = [
                    key for key in STORY_SCORE_CRITERIA
                    if not isinstance(scores, dict) or key not in scores
                ]
                if missing:
                    print(
                        "    → Judge 누락 항목 "
                        f"{len(missing)}개만 짧은 보정 요청"
                    )
                    result = complete_missing_judge_scores(
                        judge_model=judge_model,
                        story_context=story_context,
                        partial_result=result,
                    )
                    scores = result.get("category_scores") or {}
                    missing = [
                        key for key in STORY_SCORE_CRITERIA if key not in scores
                    ]
                if missing:
                    raise ValueError(
                        "Judge omitted category scores after repair: "
                        + ", ".join(missing)
                    )
                if any(not 1 <= int(scores[key]) <= 5 for key in STORY_SCORE_CRITERIA):
                    raise ValueError("Judge category scores must all be between 1 and 5.")

                # 20개 1~5점 항목의 합이 곧 100점 만점 총점이다.
                score = sum(int(scores[key]) for key in STORY_SCORE_CRITERIA)
                result["total_score"] = score
                result["passed"] = story_evaluation_passed(result, min_score)
                result["judge_model"] = judge_model
                evaluations.append(result)
                print(
                    f"    Score Judge {judge_model} → "
                    f"{result['total_score']}: {result.get('reason', '')}"
                )
                break
            except Exception as e:
                print(
                    f"    Score Judge {judge_model} 응답 재시도 "
                    f"{judge_attempt}/{judge_retries}: {e}"
                )

    if not evaluations:
        return {
            "total_score": 0,
            "tier": "Weak",
            "reason": "No configured judge model returned a valid score.",
            "judge_model": None,
            "evaluations": [],
        }

    best = max(evaluations, key=lambda item: item.get("total_score", 0))
    best_result = dict(best)
    best_result["evaluations"] = [dict(item) for item in evaluations]
    return best_result


def story_evaluation_passed(evaluation: dict, min_score: int = 70) -> bool:
    scores = evaluation.get("category_scores") or {}
    total_score = int(evaluation.get("total_score", 0))
    if total_score < min_score:
        return False

    if any(int(scores.get(key, 0)) < 3 for key in STORY_SCORE_CRITERIA):
        return False

    critical_criteria = [
        "emotional_safety",
        "readability",
        "visual_scene_clarity",
        "roleplay_compatibility",
    ]
    if any(int(scores.get(key, 0)) < 4 for key in critical_criteria):
        return False

    automatic_fail = [
        "emotional_safety",
        "readability",
        "visual_scene_clarity",
    ]
    return not any(int(scores.get(key, 0)) <= 2 for key in automatic_fail)


# ─── LLM 품질 평가 (Claude Haiku) ────────────────────────────

def judge_story_quality(stories: list[tuple[str, str]]) -> int:
    """
    stories: [(model_id, story_text), ...]
    Returns: index of best story
    """
    numbered = "\n\n".join(
        f"[Story {i+1} by {mid}]\n{text}" for i, (mid, text) in enumerate(stories) if text
    )
    prompt = STORY_JUDGE_PROMPT.format(numbered_stories=numbered)

    votes: list[int] = []
    for judge_model in MODELS.story_judge_models:
        try:
            text = generate_text(
                [{"role": "user", "content": prompt}],
                model=judge_model,
                max_tokens=200,
                temperature=0.1,
            )
            result = parse_json_object(text)
            best = int(result["best"]) - 1
            if 0 <= best < len(stories):
                votes.append(best)
                print(f"    Judge {judge_model} → Story {best + 1}: {result.get('reason', '')}")
        except Exception as e:
            print(f"    Judge {judge_model} 실패: {e}")

    if votes:
        return max(set(votes), key=votes.count)

    return 0


# ─── 이미지 프롬프트 생성 ─────────────────────────────────────
def generate_image_prompts(sentences: list[str], protagonist: str) -> list[str]:
    """각 문장에서 이미지 생성용 프롬프트 추출"""
    joined = "\n".join(f"{i+1}. {s}" for i, s in enumerate(sentences))
    prompt = f"""Convert each fairy tale sentence into a short image generation prompt.

Use this exact art direction for EVERY page so the full story keeps one unified style:
{IMAGE_STYLE_GUIDE}

Character consistency rule:
- Protagonist: {protagonist}
- Keep the protagonist's species, face shape, colors, outfit/accessories, and proportions identical on every page.
- If a recurring side character appears, keep that character identical too.
- Do not change illustration medium or rendering style between pages.

Sentences:
{joined}

Output ONLY a JSON array of strings, one prompt per sentence.
Each prompt must include the fixed style phrase, the protagonist consistency note, and the scene content.
Example: ["Bright 2D mobile children's storybook app illustration, same cute rabbit protagonist, ...", ...]"""

    try:
        text = generate_text([{"role": "user", "content": prompt}], max_tokens=800)
        text = re.sub(r"```json|```", "", text).strip()
        return json.loads(text)
    except Exception:
        return [
            (
                "Bright 2D mobile children's storybook app illustration, "
                f"same protagonist ({protagonist}), consistent character design, "
                f"scene: {s[:120]}"
            )
            for s in sentences
        ]


# ─── 묘사 퀴즈 자동 생성 ─────────────────────────────────────

def generate_description_scenes(
    sentences: list[str],
    level: int,
    image_paths: list[str],
    image_prompts: Optional[list[str]] = None,
    story_title: str = "",
) -> list[DescriptionScene]:
    cfg = LEVEL_CONFIGS[level]
    n = cfg.description_scenes
    desc_type = {1: DescriptionType.WORD_GUESS, 2: DescriptionType.SENTENCE, 3: DescriptionType.REASON}[level]
    image_prompts = image_prompts or ["" for _ in sentences]

    story_pages = "\n".join(
        (
            f"Page {i + 1}\n"
            f"Story sentence: {sentence}\n"
            f"Illustration description: {image_prompts[i] if i < len(image_prompts) else ''}"
        )
        for i, sentence in enumerate(sentences)
    )
    ar_level = {1: "0.1-0.9", 2: "0.9-1.8", 3: "1.8-2.5"}[level]
    level_instruction = {
        1: (
            "Generate only Level 1 word-guess quizzes. Choose one concrete visible "
            "noun or color from each selected page. Ask a very short question, make "
            "expected_answer a complete beginner sentence, and put the exact target "
            "word first in keywords_for_evaluation. Do not ask for reasons or abstract "
            "feelings. Use three different source pages."
        ),
        2: "Generate Level 2 short-sentence scene description quizzes.",
        3: "Generate Level 3 scene-and-reason description quizzes.",
    }[level]
    prompt = DESCRIPTION_QUIZ_PROMPT.format(
        quiz_count=n,
        story_title=story_title or "Untitled Story",
        ar_level=ar_level,
        level=level,
        level_instruction=level_instruction,
        story_pages=story_pages,
    )

    try:
        text = generate_text(
            [{"role": "user", "content": prompt}],
            max_tokens=1400,
            temperature=0.2,
        )
        data = parse_json_object(text)
        scenes = []
        for i, quiz in enumerate(data.get("quizzes", [])[:n]):
            scene_number = int(quiz.get("scene_number") or i + 1)
            scene_idx = max(0, min(len(sentences) - 1, scene_number - 1))
            expected_answer = quiz.get("expected_answer") or sentences[scene_idx]
            keywords = quiz.get("keywords_for_evaluation") or []
            blank_word = keywords[0] if desc_type == DescriptionType.WORD_GUESS and keywords else None
            scenes.append(DescriptionScene(
                scene_number=i + 1,
                page_number=scene_idx + 1,
                text=sentences[scene_idx],
                image_path=image_paths[scene_idx] if scene_idx < len(image_paths) else "",
                desc_type=desc_type,
                blank_word=blank_word,
                answer_sentence=expected_answer,
                guide_hint=quiz.get("hint_1") or expected_answer[:len(expected_answer)//2],
            ))
        if len(scenes) == n:
            return scenes
    except Exception as e:
        print(f"묘사 퀴즈 생성 실패: {e}")

    # fallback: 묘사에 적합한 장면 선택 (가운데 문장들 우선)
    mid = len(sentences) // 2
    indices = list(range(max(0, mid - n//2), min(len(sentences), mid - n//2 + n)))
    selected = [(indices[i], sentences[indices[i]]) for i in range(len(indices))]

    type_instruction = {
        DescriptionType.WORD_GUESS: """Create a fill-in-the-blank exercise. Pick one key word (color, animal, or object) from the sentence.
Return JSON: {"blank_word": "...", "answer_sentence": "The ___ is/has ...", "guide_hint": "The ___ is"}""",
        DescriptionType.SENTENCE: """Create a one-sentence scene description task.
Return JSON: {"answer_sentence": "The boy is running.", "guide_hint": "The boy is"}""",
        DescriptionType.REASON: """Create a scene description + reason task.
Return JSON: {"answer_sentence": "She looks happy because she found the treasure.", "guide_hint": "She looks happy because"}""",
    }[desc_type]

    scenes = []
    for i, (idx, sentence) in enumerate(selected):
        prompt = f"""Given this fairy tale sentence: "{sentence}"
{type_instruction}
Make it simple for young English learners."""

        try:
            text = generate_text([{"role": "user", "content": prompt}], max_tokens=300)
            text = re.sub(r"```json|```", "", text).strip()
            data = json.loads(text)
            scenes.append(DescriptionScene(
                scene_number=i + 1,
                page_number=idx + 1,
                text=sentence,
                image_path=image_paths[idx] if idx < len(image_paths) else "",
                desc_type=desc_type,
                blank_word=data.get("blank_word"),
                answer_sentence=data.get("answer_sentence", sentence),
                guide_hint=data.get("guide_hint", ""),
            ))
        except Exception:
            scenes.append(DescriptionScene(
                scene_number=i + 1,
                page_number=idx + 1,
                text=sentence,
                image_path=image_paths[idx] if idx < len(image_paths) else "",
                desc_type=desc_type,
                answer_sentence=sentence,
                guide_hint=sentence[:len(sentence)//2],
            ))
    return scenes


# ─── 롤플레잉 시나리오 생성 ──────────────────────────────────

def generate_roleplay_scenarios(
    sentences: list[str],
    level: int,
    protagonist: str,
    story_title: str = "",
) -> list[RoleplayScenario]:
    cfg = LEVEL_CONFIGS[level]
    topic_map = {1: RoleplayTopic.INTRO, 2: RoleplayTopic.DIRECTION, 3: RoleplayTopic.ESCAPE}
    char_map  = {1: "a dwarf", 2: "a hunter", 3: "the ball host"}
    story_pages = "\n".join(
        f"Page {i + 1}: {sentence}" for i, sentence in enumerate(sentences)
    )
    prompt = ROLEPLAY_MISSION_PROMPT.format(
        mission_count=cfg.roleplay_count,
        story_title=story_title or "Untitled Story",
        level=level,
        protagonist=protagonist,
        story_pages=story_pages,
    )

    try:
        text = generate_text(
            [{"role": "user", "content": prompt}],
            max_tokens=1200,
            temperature=0.2,
        )
        data = parse_json_object(text)
        scenarios = []
        for i, mission in enumerate(data.get("missions", [])[:cfg.roleplay_count]):
            example_answers = mission.get("example_correct_answers") or []
            alternative_answers = mission.get("acceptable_alternative_answers") or []
            model_answer = (
                example_answers[0]
                if example_answers
                else mission.get("expected_intent")
                or mission.get("pass_condition")
                or ""
            )
            hints = [
                mission.get("hint_1", ""),
                mission.get("hint_2", ""),
                mission.get("hint_3", ""),
            ]
            scenarios.append(RoleplayScenario(
                scenario_id=f"rp_{level}_{i+1}",
                topic=topic_map[level],
                level=level,
                scene_description=mission.get("situation_summary", ""),
                character_name=char_map[level],
                player_goal=mission.get("mission_goal", ""),
                model_answer=model_answer,
                hint_sequence=[h for h in hints if h],
            ))
        if len(scenarios) == cfg.roleplay_count:
            return scenarios
    except Exception as e:
        print(f"롤플레잉 생성 실패: {e}")

    goal_map  = {
        1: "Introduce yourself to the character in a kind way",
        2: "Ask for help or directions politely",
        3: "Help solve the story problem with a brave idea",
    }
    return [
        RoleplayScenario(
            scenario_id=f"rp_{level}_1",
            topic=topic_map[level],
            level=level,
            scene_description="A friendly character needs kind words from the child.",
            character_name=char_map[level],
            player_goal=goal_map[level],
            model_answer="I can help you.",
            hint_sequence=["Try saying something kind.", "Offer help.", "Say, 'I can help you.'"],
        )
    ]


# ─── 메인 파이프라인 ──────────────────────────────────────────

async def generate_lesson(
    book_id: str,
    episode: int,
    level: int,
    age: int,
    theme: str,
    protagonist: str,
    generate_images: bool = False,
    total_episodes: int = 1,
    continuity_context: str = "This is episode 1. Start the longer story gently.",
    image_output_dir: Optional[str] = None,
) -> Optional[Lesson]:
    """
    전체 콘텐츠 제작 파이프라인 실행
    """
    print(f"\n{'='*50}")
    print(f"[콘텐츠 생성] book={book_id} ep={episode} level={level}")

    prompt = build_story_prompt(
        book_id,
        age,
        level,
        theme,
        protagonist,
        episode=episode,
        total_episodes=total_episodes,
        continuity_context=continuity_context,
    )

    # ① Llama로 동화 텍스트 생성
    print(f"  ① 동화 텍스트 생성 ({MODELS.story_model})...")
    local_result = call_local_story_model(prompt)
    candidates = [(MODELS.story_model, local_result)] if local_result else []

    if not candidates:
        print("  ✗ 로컬 Llama 동화 생성 실패")
        return None

    # ② LLM 품질 평가 → 최고 채택
    print(f"  ② 품질 평가 ({len(candidates)}개 후보)...")
    best_idx = judge_story_quality(candidates) if len(candidates) > 1 else 0
    best_model, best_text = candidates[best_idx]
    print(f"  → 채택: {best_model}")

    # 후처리는 사람이 수행한다. 여기서는 구조를 검사하거나 자동 수리하지 않는다.
    sentences = extract_story_sentences(best_text)
    min_pages, max_pages = page_range_for_book(book_id)
    if not sentences or not min_pages <= len(sentences) <= max_pages:
        print(
            f"  ✗ 동화 초안 페이지 수가 올바르지 않습니다: "
            f"{len(sentences)}개 (필수: {min_pages}-{max_pages})"
        )
        return None
    print(f"  ✓ 동화 초안 생성 완료 ({len(sentences)}문장 추출)")

    # ④ 이미지 프롬프트 생성
    print("  ④ 이미지 프롬프트 생성...")
    image_prompts = generate_image_prompts(sentences, protagonist)

    pages = [
        StoryPage(
            page_number=i + 1,
            text=s,
            image_prompt=image_prompts[i] if i < len(image_prompts) else "",
        )
        for i, s in enumerate(sentences)
    ]
    image_paths = (
        generate_story_images(
            pages, book_id=book_id, episode=episode, output_dir=image_output_dir
        )
        if generate_images
        else attach_planned_image_paths(
            pages, book_id=book_id, episode=episode, output_dir=image_output_dir
        )
    )

    # ⑤ 묘사 퀴즈 생성
    print("  ⑤ 묘사 퀴즈 생성...")
    description_scenes = generate_description_scenes(
        sentences=sentences,
        level=level,
        image_paths=image_paths,
        image_prompts=image_prompts,
        story_title=theme,
    )

    # ⑥ 롤플레잉 시나리오 생성
    print("  ⑥ 롤플레잉 시나리오 생성...")
    roleplay = generate_roleplay_scenarios(sentences, level, protagonist)

    lesson = Lesson(
        lesson_id=f"{book_id}_ep{episode}_lv{level}",
        book_id=book_id,
        level=level,
        episode=episode,
        pages=pages,
        description_scenes=description_scenes,
        roleplay_scenarios=roleplay,
    )

    print(f"  ✓ 강의 패키지 완성: {lesson.lesson_id}")
    return lesson


async def generate_lesson_if_quality_passes(
    book_id: str,
    episode: int,
    level: int,
    age: int,
    theme: str,
    protagonist: str,
    min_score: int = 70,
    generate_images: bool = False,
    quality_retries: int = 3,
    total_episodes: int = 1,
    continuity_context: str = "This is episode 1. Start the longer story gently.",
    image_output_dir: Optional[str] = None,
    on_draft: Optional[Callable[[dict], None]] = None,
    previous_sentences: Optional[list[str]] = None,
    avoid_sentences: Optional[list[str]] = None,
    quality_feedback: Optional[list[str]] = None,
) -> tuple[Optional[Lesson], dict]:
    quality_retries = max(3, quality_retries)
    print(f"\n{'='*50}")
    print(f"[품질 필터 생성] theme={theme} ep={episode} min_score={min_score}")

    base_prompt = build_story_prompt(
        book_id,
        age,
        level,
        theme,
        protagonist,
        episode=episode,
        total_episodes=total_episodes,
        continuity_context=continuity_context,
    )
    best_failure = {
        "theme": theme,
        "accepted": False,
        "score": 0,
        "reason": "Story generation failed.",
    }
    # 이번 lesson을 반복 시도하는 동안 걸러진 중복 문장들을 계속 누적해서
    # 다음 시도의 프롬프트에 "이건 피해라"로 넣어준다. 재시도가 서로 아무
    # 피드백 없이 같은 prompt를 반복하면, 낮은 temperature에서 로컬 모델이
    # 매번 비슷한 결과물을 내며 같은 이유로 계속 리젝되기 쉽다.
    if avoid_sentences is None:
        avoid_sentences = []
    if quality_feedback is None:
        quality_feedback = []

    for quality_attempt in range(1, quality_retries + 1):
        prompt = (
            base_prompt
            + build_avoid_sentences_addendum(avoid_sentences)
            + build_quality_feedback_addendum(quality_feedback)
        )
        # 재시도할수록 temperature를 조금씩 올려서 이전 시도와 다른 문장이
        # 나올 확률을 높인다. 0.45에서 시작해 0.9를 넘지 않는다.
        attempt_temperature = min(0.45 + 0.15 * (quality_attempt - 1), 0.9)
        best_text = call_local_story_model(prompt, temperature=attempt_temperature)
        if not best_text:
            best_failure = {
                "theme": theme,
                "accepted": False,
                "score": 0,
                "reason": "Story generation failed.",
            }
            print(f"  초안 재생성 {quality_attempt}/{quality_retries}: 생성 실패")
            continue

        sentences = extract_story_sentences(best_text)
        min_pages, max_pages = page_range_for_book(book_id)
        page_count_valid = min_pages <= len(sentences) <= max_pages
        if on_draft:
            on_draft({
                "book_id": book_id,
                "episode": episode,
                "level": level,
                "theme": theme,
                "quality_attempt": quality_attempt,
                "story_model": MODELS.story_model,
                "raw_story": best_text,
                "extracted_sentences": sentences,
                "parse_status": "valid" if sentences else "invalid",
                "page_count": len(sentences),
                "page_count_status": "valid" if page_count_valid else "invalid",
                "required_page_count": min_pages if min_pages == max_pages else f"{min_pages}-{max_pages}",
            })

        if not sentences:
            best_failure = {
                "theme": theme,
                "accepted": False,
                "score": 0,
                "reason": (
                    "Draft JSON was incomplete or invalid; it was saved but was not "
                    "sent to Qwen and will not be used as continuity context."
                ),
                "raw_story": best_text,
                "extracted_sentences": [],
            }
            print(
                f"  초안 재생성 {quality_attempt}/{quality_retries}: "
                "JSON 파싱 실패 (Qwen 평가 생략)"
            )
            continue

        if not page_count_valid:
            best_failure = {
                "theme": theme,
                "accepted": False,
                "score": 0,
                "reason": (
                    f"Draft has {len(sentences)} pages; this book requires "
                    f"{min_pages if min_pages == max_pages else f'{min_pages}-{max_pages}'} pages. "
                    "It was saved but was not sent to Qwen or continuity context."
                ),
                "raw_story": best_text,
                "extracted_sentences": sentences,
            }
            print(
                f"  초안 재생성 {quality_attempt}/{quality_retries}: "
                f"페이지 수 {len(sentences)}개 (필수: {min_pages}-{max_pages})"
            )
            continue

        similarity_threshold = 0.94
        reused_sentences = find_reused_sentences(
            sentences,
            previous_sentences or [],
            similarity_threshold=similarity_threshold,
        )
        if reused_sentences:
            avoid_sentences.extend(item["sentence"] for item in reused_sentences)
            rewritten_sentences = rewrite_reused_story_sentences(
                sentences,
                reused_sentences,
                episode=episode,
                total_episodes=total_episodes,
                level=level,
                theme=theme,
            )
            remaining_reuse = find_reused_sentences(
                rewritten_sentences,
                previous_sentences or [],
                similarity_threshold=similarity_threshold,
            )
            if not remaining_reuse:
                sentences = rewritten_sentences
                print(
                    f"  → 중복 문장 {len(reused_sentences)}개를 해당 페이지만 재작성"
                )
            else:
                avoid_sentences.extend(
                    item["sentence"] for item in remaining_reuse
                )
                best_failure = {
                    "theme": theme,
                    "accepted": False,
                    "score": 0,
                    "reason": "Duplicate page rewrite still reused earlier text.",
                    "reused_sentences": remaining_reuse,
                    "story_sentences": rewritten_sentences,
                }
                print(
                    f"  초안 재생성 {quality_attempt}/{quality_retries}: "
                    f"부분 재작성 후에도 유사 문장 {len(remaining_reuse)}개"
                )
                continue

        print("  → 초안 저장 완료, Qwen 품질 평가 시작")
        story_text = story_text_from_sentences(sentences)
        evaluation = evaluate_story_score(
            story_text,
            episode=episode,
            total_episodes=total_episodes,
            episode_beat=theme,
            previous_sentences=previous_sentences,
            min_score=min_score,
        )
        score = int(evaluation.get("total_score", 0))

        passed = bool(evaluation.get("passed")) and story_evaluation_passed(evaluation, min_score)
        if passed:
            break

        best_failure = {
            "theme": theme,
            "accepted": False,
            "score": score,
            "reason": evaluation.get("reason", "Score below threshold."),
            "evaluation": evaluation,
            "story_sentences": sentences,
        }
        quality_feedback.extend(evaluation_feedback(evaluation))
        print(f"  품질 재생성 {quality_attempt}/{quality_retries}: {score}/{min_score}")
    else:
        return best_failure and (None, best_failure)

    print(f"  ✓ 품질 통과: {score}/{min_score}")

    image_prompts = generate_image_prompts(sentences, protagonist)
    pages = [
        StoryPage(
            page_number=i + 1,
            text=s,
            image_prompt=image_prompts[i] if i < len(image_prompts) else "",
        )
        for i, s in enumerate(sentences)
    ]
    image_paths = (
        generate_story_images(
            pages, book_id=book_id, episode=episode, output_dir=image_output_dir
        )
        if generate_images
        else attach_planned_image_paths(
            pages, book_id=book_id, episode=episode, output_dir=image_output_dir
        )
    )
    print("  → 묘사 퀴즈 생성...")
    description_scenes = generate_description_scenes(
        sentences=sentences,
        level=level,
        image_paths=image_paths,
        image_prompts=image_prompts,
        story_title=theme,
    )
    roleplay = generate_roleplay_scenarios(sentences, level, protagonist)

    lesson = Lesson(
        lesson_id=f"{book_id}_ep{episode}_lv{level}",
        book_id=book_id,
        level=level,
        episode=episode,
        pages=pages,
        description_scenes=description_scenes,
        roleplay_scenarios=roleplay,
    )

    return lesson, {
        "theme": theme,
        "accepted": True,
        "score": score,
        "reason": evaluation.get("reason", ""),
        "evaluation": evaluation,
    }


# ─── TTS 생성 ─────────────────────────────────────────────────

def generate_tts_for_lesson(lesson: Lesson, output_dir: str = "audio") -> Lesson:
    """ElevenLabs TTS로 각 페이지 음성 생성"""
    import requests
    import os

    os.makedirs(output_dir, exist_ok=True)
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")

    for page in lesson.pages:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{MODELS.elevenlabs_voice_id}"
        headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
        payload = {
            "text": page.text,
            "model_id": "eleven_turbo_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
        }
        resp = requests.post(url, headers=headers, json=payload)
        if resp.status_code == 200:
            path = f"{output_dir}/{lesson.lesson_id}_p{page.page_number}.mp3"
            with open(path, "wb") as f:
                f.write(resp.content)
            page.audio_path = path
            print(f"  TTS 저장: {path}")
        else:
            print(f"  TTS 실패 p{page.page_number}: {resp.status_code}")

    return lesson


if __name__ == "__main__":
    from scripts.generate_lessons import main

    main()
