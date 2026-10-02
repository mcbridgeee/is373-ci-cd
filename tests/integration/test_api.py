import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok_with_release_metadata():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "commit" in body
    assert "built_at" in body


def test_questions_endpoint_returns_four_questions_with_four_choices_each():
    response = client.get("/api/questions")
    assert response.status_code == 200
    questions = response.json()["questions"]
    assert len(questions) == 4
    for question in questions:
        assert len(question["choices"]) == 4


def test_quiz_submission_agrees_when_client_result_matches():
    response = client.post(
        "/api/quiz",
        json={"answers": ["a", "b", "c", "d"], "client_result": "Sensodyne"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["server_result"] == "Sensodyne"
    assert body["agree"] is True


def test_quiz_submission_reports_disagreement_without_hiding_it():
    response = client.post(
        "/api/quiz",
        json={"answers": ["a", "b", "c", "d"], "client_result": "Crest"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["server_result"] == "Sensodyne"
    assert body["agree"] is False


def test_quiz_submission_rejects_wrong_answer_count():
    response = client.post(
        "/api/quiz",
        json={"answers": ["a", "b", "c"], "client_result": "Sensodyne"},
    )
    assert response.status_code == 422
    assert "answers" in response.json()["detail"]


def test_quiz_submission_rejects_invalid_choice_key():
    response = client.post(
        "/api/quiz",
        json={"answers": ["a", "z", "c", "d"], "client_result": "Sensodyne"},
    )
    assert response.status_code == 422
    assert "answers[1]" in response.json()["detail"]


def test_quiz_submission_rejects_unknown_fields():
    response = client.post(
        "/api/quiz",
        json={"answers": ["a", "b", "c", "d"], "client_result": "Sensodyne", "admin": True},
    )
    assert response.status_code == 422


@pytest.mark.parametrize(
    "payload",
    [
        {"answers": ["a"] * 17, "client_result": "Sensodyne"},
        {"answers": ["a" * 33, "b", "c", "d"], "client_result": "Sensodyne"},
        {"answers": ["a", "b", "c", "d"], "client_result": "S" * 33},
    ],
)
def test_quiz_submission_rejects_oversized_input(payload):
    assert client.post("/api/quiz", json=payload).status_code == 422


def test_validation_errors_do_not_echo_submitted_input():
    marker = "<script>alert(1)</script>"
    response = client.post("/api/quiz", json={"answers": [marker * 3], "client_result": 7})
    assert response.status_code == 422
    assert "<script>" not in response.text


@pytest.mark.parametrize("path", ["/", "/health", "/api/questions"])
def test_every_response_carries_security_headers(path):
    headers = client.get(path).headers
    csp = headers["content-security-policy"]
    assert "default-src 'none'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "unsafe-inline" not in csp
    assert "'sha256-" in csp
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["referrer-policy"] == "no-referrer"
    assert "camera=()" in headers["permissions-policy"]
