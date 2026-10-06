"""Pure arithmetic for the calculator page. No HTTP, no I/O (docs/spec.md CALC-xx)."""

import math
from typing import Literal

Operation = Literal["add", "subtract", "multiply", "divide"]
LIMIT = 1_000_000


class CalculationError(ValueError):
    """Raised for inputs the calculator refuses. Carries a stable code for the API (CALC-21)."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


def calculate(a: float, b: float, operation: Operation) -> float:
    for number in (a, b):
        if isinstance(number, bool) or not isinstance(number, (int, float)):
            raise CalculationError("invalid_operand", "Enter numbers only.")
        if not math.isfinite(number) or abs(number) > LIMIT:
            raise CalculationError("invalid_operand", "Numbers must be finite and within ±1,000,000.")

    if operation == "add":
        result = a + b
    elif operation == "subtract":
        result = a - b
    elif operation == "multiply":
        result = a * b
    elif operation == "divide":
        if b == 0:
            raise CalculationError("division_by_zero", "Cannot divide by zero.")
        result = a / b
    else:
        raise CalculationError("invalid_operation", "Choose add, subtract, multiply, or divide.")

    return float(result)
