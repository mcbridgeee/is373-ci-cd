# Testing strategy

Three boundaries, each tested at the layer where it actually lives — no layer re-tests what another layer already proves.

## Unit — `tests/unit/`

Tests `app/quiz.py` directly, as plain Python. No FastAPI, no HTTP, no container.

- Every valid combination of 4 answers resolves to `"Sensodyne"`.
- Invalid input (wrong length, out-of-range choice key) raises the validation error the API layer translates into a `422`.

Run with `make test-unit`.

## Integration — `tests/integration/`

Tests `app/main.py` through FastAPI's `TestClient`, in-process — no container, no network.

- `GET /health` returns `200` with `status`, `commit`, `built_at`.
- `POST /api/quiz` with valid answers returns `200`, `server_result: "Sensodyne"`, `agree: true`.
- `POST /api/quiz` with invalid answers (missing, extra, out-of-range) returns `422` naming the failing question, per QUIZ-21.
- `POST /api/quiz` where `client_result` disagrees with what the server would compute still returns `agree: false` rather than silently correcting it — the API reports disagreement, it doesn't hide it.

Run with `make test-integration`.

## End-to-end — `tests/e2e/`

Playwright (Chromium) driving the **actual built container image**, started in isolation on a dedicated port — not the dev server, not a bare `uvicorn` process. This is what proves the frontend and the published artifact actually agree with each other, not just that the source code does.

- Load the quiz, answer all 4 questions, submit, and confirm the page displays "Sensodyne" and an agreement confirmation.
- Confirm submission is disabled until all 4 questions are answered (QUIZ-02).
- Confirm the footer's displayed commit/build time matches `GET /health` on the same running container (QUIZ-31).

Run with `make test-e2e`. Failure traces/screenshots are retained under `artifacts/playwright`; CI uploads them for 7 days. The release image itself ships no browser or test packages — Playwright and its browsers live only in the CI/dev environment.

## Boundary rule

If a behavior can be proven with a pure Python unit test, it is not re-proven with `TestClient`. If it can be proven with `TestClient`, it is not re-proven with a full browser + container E2E test. E2E exists only to catch what the lower two boundaries structurally cannot: container build correctness, real HTTP over a real port, and actual rendered DOM behavior.

## Failure evidence

A deliberately broken PR at any of the three boundaries must fail its corresponding CI step and must not publish. See [ci-cd.md](ci-cd.md#failure-and-rollback-behavior) for the expected behavior per stage, and [implementation-plan.md](implementation-plan.md) for whether a demonstration failure has actually been rehearsed yet.
