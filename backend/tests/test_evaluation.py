from app.services.evaluation import RepeatEvaluationService


def test_repeat_evaluation_aligns_words_when_one_word_is_missing() -> None:
    result = RepeatEvaluationService().evaluate(
        target_text="She is reading a book.",
        transcript="She reading a book",
    )

    assert result["score"] == 100
    assert result["passed"] is True
    assert [word["correct"] for word in result["wordResults"]] == [
        True,
        True,
        True,
        True,
        True,
    ]


def test_repeat_evaluation_allows_small_stt_variation() -> None:
    result = RepeatEvaluationService().evaluate(
        target_text="The little dragon is happy.",
        transcript="The little dragons is happy",
    )

    assert result["passed"] is True
    assert [word["correct"] for word in result["wordResults"]] == [
        True,
        True,
        True,
        True,
        True,
    ]


def test_repeat_evaluation_fails_when_too_many_words_are_missing() -> None:
    result = RepeatEvaluationService().evaluate(
        target_text="The little dragon is very happy.",
        transcript="The dragon happy",
    )

    assert result["passed"] is False
    assert [word["correct"] for word in result["wordResults"]] == [
        True,
        False,
        True,
        False,
        False,
        True,
    ]


def test_repeat_evaluation_accepts_common_character_name_transcriptions() -> None:
    result = RepeatEvaluationService().evaluate(
        target_text="Popo and Toto help Pipi.",
        transcript="Bobo and Dodo help Pippi",
    )

    assert result["passed"] is True
    assert all(word["correct"] for word in result["wordResults"])


def test_repeat_evaluation_allows_small_non_name_spelling_error() -> None:
    result = RepeatEvaluationService().evaluate(
        target_text="We help our friend today.",
        transcript="We help our freind today",
    )

    assert result["passed"] is True


def test_repeat_evaluation_still_rejects_different_sentence() -> None:
    result = RepeatEvaluationService().evaluate(
        target_text="Popo helps the little bird.",
        transcript="Bobo runs home",
    )

    assert result["passed"] is False
