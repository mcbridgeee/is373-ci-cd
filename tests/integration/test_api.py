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
