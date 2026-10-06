# Architecture

## Components

- **`app/quiz.py`** — pure Python scoring logic. No HTTP, no I/O. Takes four answers, validates them, returns `"Sensodyne"`. This is the function pytest unit-tests directly.
- **`app/main.py`** — FastAPI app. `GET /health` and `POST /api/quiz`, both thin wrappers around `quiz.py` plus request validation and release metadata. This is what the integration tests exercise through `TestClient`, without a real container.
- **`app/calculator.py`**, **`app/calculator.html`**: the calculator added in issue 44, same split as the quiz: pure arithmetic, `POST /api/calculate` in `main.py`, and a single-file page at `/calc` that calculates in JavaScript and compares with the API.
- **`app/index.html`** — the entire frontend: markup, CSS, and JavaScript in one file, same constraint as the reference repo. Renders the four questions, tallies the client-side result, calls `POST /api/quiz`, and displays the server's answer plus the agreement check. This is what Playwright drives against the real built image.

Keeping arithmetic (`quiz.py`) separate from HTTP (`main.py`) separate from the browser (`index.html`) is deliberate: it lets each layer be tested at the right altitude — pytest for logic, `TestClient` for the API contract, Playwright for what a visitor actually experiences — matching [testing.md](testing.md).

## Runtime decisions

- **Language/framework**: Python 3, FastAPI, matching the reference repo and this course's established pattern.
- **Frontend**: no framework, no bundler, no CDN dependency — a single static HTML file served by FastAPI, so there is nothing to build beyond the Docker image itself.
- **Container platform**: `linux/amd64`. The reference repo now builds both AMD64 and ARM64; this project builds only AMD64 because its production host, a DigitalOcean droplet, is x86_64 (see issue 14). The pipeline shape is unchanged.
- **Ports**: development `8080`, production `8090`, WUD dashboard `8091`, matching the reference repo's convention so the two projects stay easy to compare.
- **Image identity**: `mcbridgeee/is373-ci-cd` on Docker Hub, tagged `sha-<full-commit>` (immutable by convention) and `prod` (mutable, moved only after a tested image is confirmed).

## Environment decisions (issue 2, recorded 2026-09-22)

- **Host** (development only since issue 14): this machine — Docker Desktop via WSL2 (Ubuntu distro). Docker Desktop's WSL integration was already enabled for this distro; `docker ps` runs directly from this shell with no further setup.
- **GitHub repo visibility**: `mcbridgeee/is373-ci-cd` stays **private** for now (deliberate choice, revisit later if needed). This means public-repo Actions minutes don't apply — usage counts against the account's private-repo Actions minutes.
- **Docker Hub image visibility**: `mcbridgeee/is373-ci-cd` is **public** on Docker Hub, created manually (not auto-created via push) so it never defaulted to private. Confirmed via `GET https://hub.docker.com/v2/repositories/mcbridgeee/is373-ci-cd/` → `"is_private": false`. Because the image is public, WUD needs no pull credentials on the host even though the GitHub repo itself is private.
- **Docker Hub username**: `mcbridgeee` (not a secret).
- **Registry credential**: `DOCKER_PAT` — a Docker Hub personal access token (Read & Write scope), added as a GitHub Actions repository secret directly through the GitHub web UI (Settings → Secrets and variables → Actions), so the raw value never passed through any local shell, chat, or file. Confirmed present via `gh secret list` (name only).

## Hosting decision (issue 14, recorded 2026-10-02)

Supersedes the **Host** line above. The local machine is now development only.

- **Production host**: the `server-of-love` DigitalOcean droplet (Ubuntu, x86_64), which already runs Traefik with Let's Encrypt for bmctiernan.com, www, and report. Its setup lives in [mcbridgeee/server-of-love](https://github.com/mcbridgeee/server-of-love), following [373_hosting](https://github.com/kaw393939/373_hosting).
- **Public name**: `https://quiz.bmctiernan.com`. The quiz's `prod` container joins Traefik's existing Docker network through a local, untracked `compose.override.yaml`. It starts no second proxy and publishes no new public port; `8090` and WUD's `8091` stay on `127.0.0.1`.
- **Platform**: `linux/amd64` only (see Runtime decisions).
- **Repository visibility**: stays private. Commit metadata includes a personal email address that would become public. Dependabot alerts and updates still work on a private repository; CodeQL and secret-scanning push protection would need the repository to be public.
- **Unchanged from issue 2**: Docker Hub `mcbridgeee/is373-ci-cd` (public image), the `DOCKER_PAT` Actions secret, and WUD needing no pull credentials.

## Docker Compose services

- `dev` — builds from local source with a bind mount and reload, port `8080`. No published image required; this is what you run while iterating.
- `prod` — runs the published `mcbridgeee/is373-ci-cd:prod` image from Docker Hub, port `8090`. This is what WUD updates.
- `wud` — [What's Up Docker](https://getwud.app/), watching only the `prod` container's digest on the `prod` tag, port `8091`.

`dev` and `prod` are isolated from each other: recreating `prod` must never touch `dev`'s container identity, health, or port.

## Adapting this template

Swapping FastAPI for another backend framework should only require changing `app/main.py`'s internals, the Dockerfile's build steps, and the Make targets that invoke tests — the contract in [spec.md](spec.md), the compose service shape, and the CI/CD pipeline in [ci-cd.md](ci-cd.md) are framework-agnostic.
