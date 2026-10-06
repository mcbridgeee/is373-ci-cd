import base64
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.calculator import LIMIT, CalculationError, Operation, calculate
from app.quiz import QUESTIONS, QuizValidationError, score_quiz

RELEASE_FILE = Path(__file__).with_name("release.json")


def release_identity(path: Path = RELEASE_FILE) -> dict:
    """The image's baked release (QUIZ-30); environment variables only outside images."""
    if path.exists():
        return json.loads(path.read_text())
    return {"commit": os.environ.get("BUILD_COMMIT", "dev"), "built_at": os.environ.get("BUILD_TIME", "unknown")}


RELEASE = release_identity()

PRODUCTION = os.environ.get("APP_ENV") == "production"

# No interactive API explorer on the public site (QUIZ-44).
app = FastAPI(
    title="Toothpaste Quiz",
    docs_url=None if PRODUCTION else "/docs",
    redoc_url=None if PRODUCTION else "/redoc",
    openapi_url=None if PRODUCTION else "/openapi.json",
)

INDEX = Path(__file__).parent / "index.html"
CALCULATOR = Path(__file__).parent / "calculator.html"
PAGES = (INDEX, CALCULATOR)


def _inline_hashes(tag: str) -> str:
    """CSP source list allowing exactly the inline <tag> blocks in the app's pages."""
    blocks = [
        block
        for page in PAGES
        for block in re.findall(rf"<{tag}>(.*?)</{tag}>", page.read_text(encoding="utf-8"), re.DOTALL)
    ]
    return " ".join(
        "'sha256-" + base64.b64encode(hashlib.sha256(block.encode("utf-8")).digest()).decode() + "'"
        for block in blocks
    )


# QUIZ-43: same-origin only, and only the page's own inline script and style.
SECURITY_HEADERS = {
    "Content-Security-Policy": "; ".join([
        "default-src 'none'",
        f"script-src {_inline_hashes('script')}",
        f"style-src {_inline_hashes('style')}",
        "connect-src 'self'",
        "img-src 'self'",
        "base-uri 'none'",
        "form-action 'self'",
        "frame-ancestors 'none'",
    ]),
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Cross-Origin-Opener-Policy": "same-origin",
}


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers.update(SECURITY_HEADERS)
    return response

# Generous outer bounds (QUIZ-40). The exact count and choice rules stay in
# quiz.py so their 422 messages name the failing question (QUIZ-21).
ShortText = Annotated[str, StringConstraints(max_length=32)]


class QuizRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answers: Annotated[list[ShortText], Field(max_length=16)]
    client_result: ShortText


class QuizResponse(BaseModel):
    server_result: str
    agree: bool


@app.exception_handler(RequestValidationError)
async def validation_error(_request, error):
    # Keep FastAPI's error shape but never echo the submitted input back (QUIZ-41).
    return JSONResponse(
        status_code=422,
        content={"detail": [{key: item[key] for key in ("type", "loc", "msg")} for item in error.errors()]},
    )


@app.get("/health")
def health():
    return {
        "status": "ok",
        "commit": RELEASE["commit"],
        "built_at": RELEASE["built_at"],
        "environment": os.environ.get("APP_ENV", "development"),
    }


@app.get("/api/questions")
def get_questions():
    return {"questions": QUESTIONS}


@app.post("/api/quiz", response_model=QuizResponse)
def submit_quiz(payload: QuizRequest):
    try:
        server_result = score_quiz(payload.answers)
    except QuizValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return QuizResponse(server_result=server_result, agree=(server_result == payload.client_result))


# CALC-20: strict JSON numbers only (no "6" strings, no booleans), bounded.
Operand = Annotated[float, Field(strict=True, ge=-LIMIT, le=LIMIT, allow_inf_nan=False)]


class CalculationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    a: Operand
    b: Operand
    operation: Operation


class CalculationResponse(BaseModel):
    result: float


@app.post("/api/calculate", response_model=CalculationResponse)
def calculate_route(payload: CalculationRequest):
    try:
        return CalculationResponse(result=calculate(payload.a, payload.b, payload.operation))
    except CalculationError as error:
        raise HTTPException(status_code=400, detail={"code": error.code, "message": str(error)}) from error


@app.get("/")
def index():
    return FileResponse(INDEX)


@app.get("/calc")
def calculator_page():
    # On calc.bmctiernan.com, Traefik maps "/" here (CALC-01).
    return FileResponse(CALCULATOR)
