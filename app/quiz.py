"""Pure quiz-scoring logic. No HTTP, no I/O — see docs/spec.md QUIZ-01/03/12/20/21."""

VALID_CHOICES = ("a", "b", "c", "d")

QUESTIONS = [
    {
        "id": "sensitivity",
        "prompt": "How do your teeth feel around hot or cold food and drinks?",
        "choices": {
            "a": "Perfectly fine",
            "b": "A little tingly",
            "c": "Ouch, every time",
            "d": "I've given up on ice cream",
        },
    },
    {
        "id": "brushing",
        "prompt": "How often do you brush your teeth?",
        "choices": {
            "a": "Twice a day, like clockwork",
            "b": "Once a day, usually",
            "c": "When I remember",
            "d": "Is that a trick question?",
        },
    },
    {
        "id": "gums",
        "prompt": "Do your gums ever bleed when you brush or floss?",
        "choices": {
            "a": "Never",
            "b": "Occasionally",
            "c": "Pretty often",
            "d": "I don't floss, so I wouldn't know",
        },
    },
    {
        "id": "flavor",
        "prompt": "What's your ideal toothpaste flavor?",
        "choices": {
            "a": "Mint",
            "b": "Cinnamon",
            "c": "Fruit",
            "d": "Flavor doesn't matter to me",
        },
    },
]

RESULT = "Sensodyne"


class QuizValidationError(ValueError):
    """Raised when submitted answers don't match the expected shape. Carries the failing index (-1 for length)."""

    def __init__(self, index: int, message: str):
        self.index = index
        super().__init__(message)


def score_quiz(answers: list[str]) -> str:
    if len(answers) != len(QUESTIONS):
        raise QuizValidationError(
            -1, f"answers must contain exactly {len(QUESTIONS)} entries, got {len(answers)}"
        )
    for i, answer in enumerate(answers):
        if answer not in VALID_CHOICES:
            raise QuizValidationError(
                i, f"answers[{i}] must be one of: {', '.join(VALID_CHOICES)}"
            )
    return RESULT
