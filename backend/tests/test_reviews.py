import pytest

from app.models import (
    DescriptionQuestion,
    DescriptionQuestionType,
    ReadingChunk,
    RepeatQuestion,
    ReviewCard,
    ReviewCardType,
    RoleplayMission,
)
from app.services.reviews import ReviewService


class FakeScalarList:
    def __init__(self, values):
        self.values = values

    def all(self):
        return self.values


class FakeResult:
    def __init__(self, values):
        self.values = values

    def scalars(self):
        return FakeScalarList(self.values)


class FakeReviewSession:
    def __init__(self) -> None:
        self.added: list[ReviewCard] = []
        self.description_questions = [
            DescriptionQuestion(
                question_id=11,
                book_id=1,
                chapter_number=1,
                step=1,
                question_type=DescriptionQuestionType.FILL_BLANK,
                instruction="Fill the blank.",
                sentence="Popo finds a ____.",
                source_text="Popo finds a little bird.",
                blank_word="bird",
            )
        ]
        self.repeat_questions = [
            RepeatQuestion(
                question_id=21,
                book_id=1,
                chapter_number=1,
                step=1,
                target_text="Popo finds a little bird.",
            ),
            RepeatQuestion(
                question_id=22,
                book_id=1,
                chapter_number=1,
                step=2,
                target_text="The friends walk through the meadow.",
            ),
            RepeatQuestion(
                question_id=23,
                book_id=1,
                chapter_number=1,
                step=3,
                target_text="They help the bird find its family.",
            ),
        ]

    async def execute(self, statement):
        entity = statement.column_descriptions[0].get("entity")
        values = {
            DescriptionQuestion: self.description_questions,
            RepeatQuestion: self.repeat_questions,
            ReadingChunk: [],
            RoleplayMission: [],
        }[entity]
        return FakeResult(values)

    async def scalar(self, statement):
        return None

    def add(self, instance) -> None:
        self.added.append(instance)


def review_card(
    *,
    card_id: int,
    source_question_id: int,
    card_type: ReviewCardType,
    sentence: str,
    cloze: str = "The ____ runs.",
    keyword: str = "lion",
) -> ReviewCard:
    return ReviewCard(
        card_id=card_id,
        profile_id=1,
        book_id=1,
        chapter_number=1,
        card_type=card_type,
        source_question_id=source_question_id,
        source_sentence=sentence,
        cloze_sentence=cloze,
        keyword=keyword,
        memory_strength_days=1,
        interval_hours=0,
        ease_factor=250,
        review_count=0,
        lapse_count=0,
    )


def test_diverse_cards_removes_semantically_identical_sentences() -> None:
    cards = [
        review_card(
            card_id=1,
            source_question_id=11,
            card_type=ReviewCardType.SENTENCE,
            sentence="Popo finds a little bird.",
        ),
        review_card(
            card_id=2,
            source_question_id=12,
            card_type=ReviewCardType.SENTENCE,
            sentence="  POPO   finds a little bird. ",
        ),
        review_card(
            card_id=3,
            source_question_id=13,
            card_type=ReviewCardType.SENTENCE,
            sentence="The friends walk home together.",
        ),
    ]

    selected = ReviewService._diverse_cards(cards, limit=5)

    assert [card.card_id for card in selected] == [1, 3]


def test_diverse_cards_does_not_refill_excluded_sources() -> None:
    cards = [
        review_card(
            card_id=1,
            source_question_id=11,
            card_type=ReviewCardType.WORD,
            sentence="The lion runs.",
        ),
        review_card(
            card_id=2,
            source_question_id=11,
            card_type=ReviewCardType.WORD,
            sentence="The lion runs.",
        ),
        review_card(
            card_id=3,
            source_question_id=12,
            card_type=ReviewCardType.WORD,
            sentence="The rabbit hops.",
            cloze="The ____ hops.",
            keyword="rabbit",
        ),
    ]

    selected = ReviewService._diverse_cards(
        cards,
        limit=5,
        exclude_source_question_ids={11},
    )

    assert [card.card_id for card in selected] == [3]


@pytest.mark.asyncio
async def test_enqueue_chapter_backfills_three_distinct_review_sentences() -> None:
    session = FakeReviewSession()
    service = ReviewService(session=session)

    created = await service.enqueue_chapter_cards(
        profile_id=1,
        book_id=1,
        chapter_number=1,
    )

    assert created == 6
    assert len(session.added) == 6
    assert len({card.source_sentence for card in session.added}) == 3
    assert {card.card_type for card in session.added} == {
        ReviewCardType.WORD,
        ReviewCardType.SENTENCE,
    }
