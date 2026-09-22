import itertools

import pytest

from app.quiz import QUESTIONS, RESULT, VALID_CHOICES, QuizValidationError, score_quiz


def test_every_valid_combination_resolves_to_sensodyne():
    for combo in itertools.product(VALID_CHOICES, repeat=len(QUESTIONS)):
        assert score_quiz(list(combo)) == RESULT


def test_result_is_the_literal_string_sensodyne():
    assert RESULT == "Sensodyne"


@pytest.mark.parametrize(
    "answers",
    [
        [],
        ["a"],
        ["a", "b", "c"],
        ["a", "b", "c", "d", "a"],
    ],
)
def test_wrong_length_raises_validation_error(answers):
    with pytest.raises(QuizValidationError) as exc_info:
        score_quiz(answers)
    assert exc_info.value.index == -1


def test_out_of_range_choice_raises_validation_error_with_failing_index():
    with pytest.raises(QuizValidationError) as exc_info:
        score_quiz(["a", "z", "b", "c"])
    assert exc_info.value.index == 1


def test_case_sensitive_choice_keys_are_rejected():
    with pytest.raises(QuizValidationError):
        score_quiz(["A", "b", "c", "d"])
