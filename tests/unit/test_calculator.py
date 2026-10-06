import math

import pytest

from app.calculator import LIMIT, CalculationError, calculate


@pytest.mark.parametrize(
    "a, b, operation, expected",
    [
        (6, 7, "add", 13),
        (6, 7, "subtract", -1),
        (6, 7, "multiply", 42),
        (42, 6, "divide", 7),
        (-2.5, 4, "multiply", -10),
        (0, 5, "divide", 0),
    ],
)
def test_four_operations(a, b, operation, expected):
    assert calculate(a, b, operation) == expected


def test_floating_point_is_reported_honestly():
    # 0.1 + 0.2 is not exactly 0.3 in binary floating point; the API returns the real value.
    assert math.isclose(calculate(0.1, 0.2, "add"), 0.3)


def test_division_by_zero_is_refused_with_a_code():
    with pytest.raises(CalculationError) as error:
        calculate(1, 0, "divide")
    assert error.value.code == "division_by_zero"


@pytest.mark.parametrize("bad", [LIMIT + 1, -LIMIT - 1, math.inf, math.nan, True, "6"])
def test_out_of_range_and_non_numbers_are_refused(bad):
    with pytest.raises(CalculationError) as error:
        calculate(bad, 1, "add")
    assert error.value.code == "invalid_operand"


def test_unknown_operation_is_refused():
    with pytest.raises(CalculationError) as error:
        calculate(1, 1, "power")
    assert error.value.code == "invalid_operation"


def test_limits_themselves_are_allowed():
    assert calculate(LIMIT, -LIMIT, "add") == 0
