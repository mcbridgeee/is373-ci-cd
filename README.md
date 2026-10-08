# Calculator CI/CD (IS373 practical test)

The deployed website is a small calculator: the browser computes the answer, the server API recomputes it, and the page shows whether they match. The same container also serves a toothpaste quiz at `/` on `quiz.bmctiernan.com`.

**Production:** https://bmctiernan.com\
**QA:** https://qa.bmctiernan.com

Image registry: [hub.docker.com/r/mcbridgeee/is373-ci-cd](https://hub.docker.com/r/mcbridgeee/is373-ci-cd) · [Workflow runs](https://github.com/mcbridgeee/is373-ci-cd/actions/workflows/ci.yml) · [Test Evidence](#test-evidence)

## Rubric checklist

| Rubric row | Where the proof is |
| --- | --- |
| **Own server** | DigitalOcean droplet (Ubuntu 24.04, user `bridge`) runs the containers; see the live sites above and the screenshots in [Test Evidence](#test-evidence) |
| **SSH security** | [SSH screenshots](#test-evidence): key login as non-root `bridge`, `permitrootlogin no`, `passwordauthentication no` |
| **GitHub repository** | Source: [`app/`](app) · [`Dockerfile`](Dockerfile) · Deployment config: [`compose.yaml`](compose.yaml), [`deploy/compose.traefik.yaml`](deploy/compose.traefik.yaml) · Workflow: [`.github/workflows/ci.yml`](.github/workflows/ci.yml) · Docker Hub token stored as the `DOCKER_PAT` Actions secret |
| **CI/CD and image** | [How CI/CD works](#how-cicd-works) · QA and production run links, image tags and registry in [Test Evidence](#test-evidence) · visible change shown QA → production with screenshots |
| **QA and production sites** | QA https://qa.bmctiernan.com and production https://bmctiernan.com, both HTTPS, separate containers · [Promotion rule](#promotion-rule) |

## Promotion rule

- Push to the **`qa`** branch → CI tests, builds, and pushes `mcbridgeee/is373-ci-cd:qa` (plus `qa-sha-<commit>`) → the droplet's QA container updates → **https://qa.bmctiernan.com**.
- After checking QA, open a PR from `qa` into **`main`** and merge it → CI pushes `:prod` (plus `sha-<commit>`) → the production container updates → **https://bmctiernan.com**.
- QA and production are separate containers that follow separate tags (`:qa` and `:prod`), so nothing on QA reaches production until it is merged into `main`.

## How CI/CD works

A push to `qa` or `main` (and every pull request) starts `.github/workflows/ci.yml`. The `verify` job runs unit tests, API integration tests, builds the Docker image once from the `Dockerfile`, runs browser (Playwright) tests against that image, and scans it with Trivy; if any step fails the job stops and the `publish` job never runs, so nothing is deployed. On a `qa` or `main` push, `publish` loads the exact tested image (no rebuild), logs in to Docker Hub with the `DOCKER_PAT` GitHub Actions secret, and pushes an immutable commit tag plus the moving `:qa` or `:prod` tag. On the DigitalOcean droplet, WUD (What's Up Docker, [compose.yaml](compose.yaml)) checks Docker Hub every 5 minutes and automatically recreates the `qa` or `prod` container when its tag points at a new image; Traefik ([deploy/compose.traefik.yaml](deploy/compose.traefik.yaml)) serves them over HTTPS with Let's Encrypt certificates. Deployment is pull-based: GitHub never holds SSH access to the server.

## Test Evidence

| | QA | Production |
| --- | --- | --- |
| Workflow run | [run 37819838978](https://github.com/mcbridgeee/is373-ci-cd/actions/runs/37819838978) (push to `qa`: verify ✅ → publish ✅) | [run 37820800076](https://github.com/mcbridgeee/is373-ci-cd/actions/runs/37820800076) (merge of [PR #51](https://github.com/mcbridgeee/is373-ci-cd/pull/51) `qa` → `main`: verify ✅ → publish ✅) |
| Deployed commit / tag | `3a0eac69759af84b963eea6d7e914ae8767ba8f4` → `:qa-sha-3a0eac6…` and `:qa` | `981e48d141dfc1fa8ae772caf37a3bf0a6acc39b` → `:sha-981e48d…` and `:prod` |
| Registry | [mcbridgeee/is373-ci-cd:qa](https://hub.docker.com/r/mcbridgeee/is373-ci-cd/tags) | [mcbridgeee/is373-ci-cd:prod](https://hub.docker.com/r/mcbridgeee/is373-ci-cd/tags) |

**Visible change** (the bold line "Version 2: this line went through QA before production." on the calculator): first on QA while production still showed the old page, then on production after merging `qa` into `main`.

| QA after the push to `qa` (commit `3a0eac6`) | Production before the merge (commit `62446f9`, no line) | Production after the merge (commit `981e48d`) |
| --- | --- | --- |
| ![QA with change](docs/evidence/qa-change.png) | ![Production before](docs/evidence/prod-before.png) | ![Production with change](docs/evidence/prod-change.png) |

**Automatic deployment proof:** WUD replaces the container on its own when CI moves a tag, with no command on the server. Recorded on the droplet: `4847d19` → `4de9076` after [run 37507643538](https://github.com/mcbridgeee/is373-ci-cd/actions/runs/37507643538) and `4de9076` → `c3311d5` after [run 37512344418](https://github.com/mcbridgeee/is373-ci-cd/actions/runs/37512344418), both with no manual step ([docs/evidence.md](docs/evidence.md#droplet)). For today's QA → production demo, the pages updated the same way; to save class time the new image was also pulled immediately with `docker compose pull`, which only skips WUD's 5-minute wait. The follow-up merge of [PR #53](https://github.com/mcbridgeee/is373-ci-cd/pull/53) was left entirely to WUD.

**SSH security** (droplet user `bridge`, key-only):

![SSH key login as bridge](docs/evidence/ssh-login.png)

![Effective sshd settings](docs/evidence/sshd-settings.png)

`sudo sshd -T | grep -Ei 'permitrootlogin|passwordauthentication'` reports `permitrootlogin no` and `passwordauthentication no`. Attempts to log in as `root`, or with a password, are refused (shown live in class). Full hardening checklist: [server-of-love/security](https://github.com/mcbridgeee/server-of-love/tree/main/security). More history: [docs/evidence.md](docs/evidence.md).

---

## About the app

A small FastAPI toothpaste-recommendation quiz that makes the path from a local edit to a tested production release visible. One HTML page tallies an answer in JavaScript, a backend API independently recomputes it, and the page shows whether the two agree. No matter what you answer, the recommendation is always **Sensodyne** — that's the whole joke. The point of the project is the CI/CD pipeline and the dual-computation pattern around it, not the quiz.

The same app also serves a **calculator** (`/calc`, and `https://calc.bmctiernan.com` once deployed) that matches the reference repo's demo: the browser calculates, the API recalculates, and the page shows **Results match**. Same image, same tests, same pipeline (#44).

This repo follows the development and delivery process demonstrated in [kaw393939/is373_ci_cd](https://github.com/kaw393939/is373_ci_cd) — structure and workflow only; the application content is intentionally different.

**Status:** live on the DigitalOcean droplet: production at https://bmctiernan.com (also `quiz.` and `calc.`), QA at https://qa.bmctiernan.com. See the [hosting runbook](docs/hosting.md).

## Delivery flow (target)

```mermaid
flowchart LR
    edit[Local edit / :8080] --> pr[Issue-linked PR]
    pr --> checks[Unit → integration → build → E2E]
    checks --> merge[Merge passing PR]
    merge --> verify[Verify main release]
    verify --> hub[Publish exact tested image]
    hub --> wud[WUD detects prod digest change]
    wud --> prod[Production / :8090]
```

Only a passing `main` push publishes. PRs and manual verification never publish. Each release gets a `sha-<full-commit>` tag and the mutable `prod` channel.

## Run the demo locally

```sh
git clone git@github.com:mcbridgeee/is373-ci-cd.git
cd is373-ci-cd
make setup
make browsers
make up
```

| Service | Default address | Behavior |
| --- | --- | --- |
| Development | [localhost:8080](http://localhost:8080) | Mounted local source with reload |
| Production | [localhost:8090](http://localhost:8090) | Last passing image from Docker Hub |
| WUD dashboard | [localhost:8091](http://localhost:8091) | Authenticated image monitoring and updates |

## Test and operate

```sh
make test-unit          # Pure Python quiz-scoring logic and validation
make test-integration   # Real FastAPI request/response contracts
make build               # Build the release image once
make test-e2e            # Chromium against that image on an isolated port
make status               # Running services and production release
make check-updates       # Ask WUD to check the registry now
make down                 # Stop this project's services; keep WUD data
```

## Specifications and development

- [Product specification](docs/spec.md): numbered requirement IDs and HTTP contract.
- [Architecture](docs/architecture.md): components, runtime decisions.
- [Testing strategy](docs/testing.md): the three boundaries.
- [CI/CD specification](docs/ci-cd.md): gates, versioning, publication, rollback.
- [Hosting](docs/hosting.md): the droplet runbook for `https://quiz.bmctiernan.com`.
- [Security](docs/security.md): controls by layer and the image scan policy.
- [Demo script](docs/demo.md): what to show, in order, with likely questions.
- [Evidence](docs/evidence.md): run links, releases, blocked PRs, and rehearsal results.
- [Implementation plan](docs/implementation-plan.md): the ordered issue backlog.
- [Contributing](CONTRIBUTING.md), [AI instructions](AGENTS.md), and [GitHub policy](docs/github-workflow.md).

[Issues](https://github.com/mcbridgeee/is373-ci-cd/issues) · [Milestone](https://github.com/mcbridgeee/is373-ci-cd/milestone/1) · [Actions](https://github.com/mcbridgeee/is373-ci-cd/actions) · [Commit history](https://github.com/mcbridgeee/is373-ci-cd/commits/main/)
