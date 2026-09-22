# Architecture

## Components

- **`app/quiz.py`** — pure Python scoring logic. No HTTP, no I/O. Takes four answers, validates them, returns `"Sensodyne"`. This is the function pytest unit-tests directly.
- **`app/main.py`** — FastAPI app. `GET /health` and `POST /api/quiz`, both thin wrappers around `quiz.py` plus request validation and release metadata. This is what the integration tests exercise through `TestClient`, without a real container.
- **`app/index.html`** — the entire frontend: markup, CSS, and JavaScript in one file, same constraint as the reference repo. Renders the four questions, tallies the client-side result, calls `POST /api/quiz`, and displays the server's answer plus the agreement check. This is what Playwright drives against the real built image.

Keeping arithmetic (`quiz.py`) separate from HTTP (`main.py`) separate from the browser (`index.html`) is deliberate: it lets each layer be tested at the right altitude — pytest for logic, `TestClient` for the API contract, Playwright for what a visitor actually experiences — matching [testing.md](testing.md).

## Runtime decisions

- **Language/framework**: Python 3, FastAPI, matching the reference repo and this course's established pattern.
- **Frontend**: no framework, no bundler, no CDN dependency — a single static HTML file served by FastAPI, so there is nothing to build beyond the Docker image itself.
- **Container platform**: `linux/amd64`. The reference repo targets `linux/arm64` because it was built and verified on Apple Silicon; this project's host is a Windows/WSL2 machine (x86_64), so the Dockerfile, CI build step, and `docker compose` configuration all target `linux/amd64` instead. This is the one deliberate deviation from the reference repo's platform choice — the pipeline shape is unchanged.
- **Ports**: development `8080`, production `8090`, WUD dashboard `8091`, matching the reference repo's convention so the two projects stay easy to compare.
- **Image identity**: `mcbridgeee/is373-ci-cd` on Docker Hub, tagged `sha-<full-commit>` (immutable by convention) and `prod` (mutable, moved only after a tested image is confirmed).

## Docker Compose services

- `dev` — builds from local source with a bind mount and reload, port `8080`. No published image required; this is what you run while iterating.
- `prod` — runs the published `mcbridgeee/is373-ci-cd:prod` image from Docker Hub, port `8090`. This is what WUD updates.
- `wud` — [What's Up Docker](https://getwud.app/), watching only the `prod` container's digest on the `prod` tag, port `8091`.

`dev` and `prod` are isolated from each other: recreating `prod` must never touch `dev`'s container identity, health, or port.

## Adapting this template

Swapping FastAPI for another backend framework should only require changing `app/main.py`'s internals, the Dockerfile's build steps, and the Make targets that invoke tests — the contract in [spec.md](spec.md), the compose service shape, and the CI/CD pipeline in [ci-cd.md](ci-cd.md) are framework-agnostic.
