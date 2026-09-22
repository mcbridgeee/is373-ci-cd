import os
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.quiz import QUESTIONS, QuizValidationError, score_quiz

BUILD_COMMIT = os.environ.get("BUILD_COMMIT", "dev")
BUILD_TIME = os.environ.get("BUILD_TIME", "unknown")

app = FastAPI(title="Toothpaste Quiz")


class QuizRequest(BaseModel):
    answers: List[str]
    client_result: str


class QuizResponse(BaseModel):
    server_result: str
    agree: bool


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
