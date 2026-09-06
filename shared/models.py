"""
공통 데이터 모델
"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class DescriptionType(str, Enum):
    WORD_GUESS   = "word_guess"    # 1단계: 빈칸 단어 추론
    SENTENCE     = "sentence"      # 2단계: 한 문장 상황 설명
    REASON       = "reason"        # 3단계: 장면 묘사 + 이유


class RoleplayTopic(str, Enum):
    INTRO        = "self_intro"    # 1단계: 자기소개
    DIRECTION    = "direction"     # 2단계: 길 묻기
    ESCAPE       = "escape"        # 3단계: 무도회장 탈출


def build_roleplay_conversation_flow(
    opening_line: str,
    max_turns: int = 3,
) -> list[dict]:
    """AI 오프닝 뒤에 사용자 입력과 AI 동적 응답이 교차하는 슬롯 생성."""
    flow: list[dict] = [{
        "sequence": 1,
        "turn": 0,
        "role": "assistant",
        "type": "opening",
        "content": opening_line,
    }]
    sequence = 2
    for turn in range(1, max_turns + 1):
        flow.append({
            "sequence": sequence,
            "turn": turn,
            "role": "user",
            "type": "input",
            "input_key": f"user_input_{turn}",
            "content": None,
        })
        sequence += 1
        flow.append({
            "sequence": sequence,
            "turn": turn,
            "role": "assistant",
            "type": (
                "closing_response"
                if turn == max_turns
                else "generated_response"
            ),
            "response_key": f"ai_response_{turn}",
            "responds_to": f"user_input_{turn}",
            "content": None,
        })
        sequence += 1
    return flow


@dataclass
class StoryPage:
    page_number: int
    text: str                        # 동화 문장
    image_prompt: str                # 이미지 생성용 프롬프트
    image_path: Optional[str] = None  # 생성된/생성 예정 이미지 경로
    audio_path: Optional[str] = None # TTS 결과 파일 경로


@dataclass
class DescriptionScene:
    scene_number: int
    page_number: int                  # 문제의 근거가 된 원본 story page 번호
    text: str                         # 해당 원본 story page 문장
    image_path: str
    desc_type: DescriptionType
    blank_word: Optional[str] = None   # 1단계: 빈칸에 들어갈 단어
    answer_sentence: str = ""          # 정답 문장 (가이드라인 포함)
    guide_hint: str = ""               # 회색 글자 가이드라인 (answer 앞부분)


@dataclass
class RoleplayScenario:
    scenario_id: str
    topic: RoleplayTopic
    level: int
    scene_description: str           # 장면 설명
    character_name: str              # AI가 맡을 캐릭터
    player_goal: str                 # 플레이어가 달성해야 할 목표
    model_answer: str                # 모범 답안 (LLM 판단 기준)
    similar_answers: list[str] = field(default_factory=list)  # 같은 의미의 허용 답안 3개
    hint_sequence: list[str] = field(default_factory=list)  # 실패한 턴별 순차 힌트
    character_personality: str = ""  # 장면에서 유지할 성격·동기·말투
    opening_line: str = ""           # 캐릭터가 사용자에게 직접 건네는 첫 대사
    max_turns: int = 3               # 사용자 발화 + 캐릭터 응답 기준 최대 턴
    conversation_flow: list[dict] = field(default_factory=list)  # AI/사용자 입력 순서


@dataclass
class Lesson:
    lesson_id: str
    book_id: str
    level: int
    episode: int
    story_title: str = ""               # LLM이 생성한 동화책 제목
    pages: list[StoryPage] = field(default_factory=list)
    description_scenes: list[DescriptionScene] = field(default_factory=list)
    roleplay_scenarios: list[RoleplayScenario] = field(default_factory=list)


@dataclass
class PronunciationResult:
    sentence: str
    transcribed: str
    score: int           # 0~100
    passed: bool
    word_scores: dict[str, float] = field(default_factory=dict)  # 단어별 유사도


@dataclass
class DescriptionResult:
    scene_number: int
    user_answer: str
    passed: bool
    feedback: str


@dataclass
class RoleplayTurn:
    turn_number: int
    user_utterance: str
    ai_response: str
    passed: bool = False
    hint_given: bool = False


@dataclass
class LessonResult:
    lesson_id: str
    pronunciation_results: list[PronunciationResult] = field(default_factory=list)
    description_results:   list[DescriptionResult]   = field(default_factory=list)
    roleplay_turns:        list[RoleplayTurn]         = field(default_factory=list)
    total_score: int = 0
    passed: bool = False
