# Product specification

A toothpaste-recommendation quiz. A few multiple-choice questions about dental habits; no matter what the visitor picks, the recommendation is always **Sensodyne**. The joke is the whole product — the value of the project is the dual-computation pattern and the CI/CD pipeline around it, not the quiz logic itself.

Requirement IDs are stable identifiers. Add new IDs for new behavior; never renumber or reuse an existing ID.

## Questions (QUIZ-0x)

- **QUIZ-01**: The quiz presents exactly 4 multiple-choice questions about dental habits (e.g. sensitivity to hot/cold, brushing frequency, gum bleeding, preferred flavor). Each question has exactly 4 answer choices.
- **QUIZ-02**: A visitor must answer all 4 questions before the quiz can be submitted. The frontend disables submission until every question has a selected answer.
- **QUIZ-03**: Regardless of which answers are selected, the recommended product is always the literal string `"Sensodyne"`. No answer combination produces a different result.

## Dual computation (QUIZ-1x)

This mirrors the reference repo's calculator: the browser computes an answer independently, in parallel, then the server verifies the client's math against its own — the point being to demonstrate a testable client/server contract, not to build meaningful quiz logic.

- **QUIZ-10**: The frontend JavaScript computes a `client_result` from the four selected answers using the same trivial rule the backend uses (always `"Sensodyne"`), without calling the API first.
- **QUIZ-11**: On submission, the frontend sends the four selected answers **and** its own `client_result` to `POST /api/quiz`.
- **QUIZ-12**: The backend independently recomputes `server_result` from the submitted answers only (never trusts the client's claimed result as an input to its own computation).
- **QUIZ-13**: The backend response includes both `server_result` and an `agree` boolean (`client_result == server_result`).
- **QUIZ-14**: The frontend renders the server's `server_result` and the `agree` outcome to the visitor. If `agree` is ever `false`, the UI shows a visible warning rather than silently trusting either side.

## Validation (QUIZ-2x)

- **QUIZ-20**: `POST /api/quiz` requires exactly 4 answers, each one of the valid choice keys (`a`–`d`) for its corresponding question.
- **QUIZ-21**: A request with a missing, extra, or out-of-range answer is rejected with `422` and a body identifying which question failed validation. No result is computed for an invalid request.

## Health and release identity (QUIZ-3x)

- **QUIZ-30**: `GET /health` returns `200` with a JSON body containing `status: "ok"`, the running `commit` (full 40-character git SHA, so it matches the `sha-<full-commit>` release tag; changed from the short SHA in #5), and `built_at` (UTC build timestamp).
- **QUIZ-31**: The frontend footer displays the same `commit` and `built_at` reported by `/health`, so a visitor (or grader) can confirm which release is actually running without reading logs.

## Security (QUIZ-4x)

Added in issue 17, before the quiz is served publicly.

- **QUIZ-40**: `POST /api/quiz` rejects unknown fields and oversized input with `422`: at most 16 `answers`, each answer and `client_result` at most 32 characters. These outer bounds sit in front of QUIZ-20/21, which still decide the exact rules.
- **QUIZ-41**: Validation error bodies never echo the submitted input back.
- **QUIZ-42**: The page renders server- and client-supplied values as text (`textContent`), never as HTML.
- **QUIZ-43**: Every response carries a Content Security Policy that allows only same-origin requests and the page's own inline script and style by SHA-256 hash (no `unsafe-inline`), plus `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `frame-ancestors 'none'`, and a `Permissions-Policy` that disables camera, microphone, and geolocation.
- **QUIZ-44**: With `APP_ENV=production`, the interactive API docs (`/docs`, `/redoc`, `/openapi.json`) are not served.

HSTS is set by the TLS terminator (Traefik on the droplet), not the app, because only it knows the connection is HTTPS.

## HTTP contract

### `GET /health`

```json
{ "status": "ok", "commit": "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678", "built_at": "2026-09-22T16:00:00Z" }
```

### `POST /api/quiz`

Request:

```json
{
  "answers": ["a", "c", "b", "d"],
  "client_result": "Sensodyne"
}
```

Response `200`:

```json
{
  "server_result": "Sensodyne",
  "agree": true
}
```

Response `422` (invalid `answers`):

```json
{
  "detail": "answers[2] must be one of: a, b, c, d"
}
```

## Deferred (out of v1 scope)

Persisted quiz history, user accounts, more than 4 questions, any recommendation logic that isn't the Sensodyne joke, a frontend framework/bundler, a database. Add these only through a new issue with a clear teaching purpose, matching the reference repo's deferral policy.
