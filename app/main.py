import os
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.quiz import QUESTIONS, QuizValidationError, score_quiz

BUILD_COMMIT = os.environ.get("BUILD_COMMIT", "dev")
BUILD_TIME = os.environ.get("BUILD_TIME", "unknown")

app = FastAPI(title="Toothpaste Quiz")

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
    return {"status": "ok", "commit": BUILD_COMMIT, "built_at": BUILD_TIME}


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


@app.get("/")
def index():
    return FileResponse(Path(__file__).parent / "index.html")
