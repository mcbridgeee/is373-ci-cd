# Implementation plan

Status: #1–#4 done (docs, decisions, quiz logic, quiz page and tests). #5 onward in progress. #14 moved production to the droplet and added the security and hosting issues below.

Milestone: [v1 — Toothpaste quiz CI/CD demonstration](https://github.com/mcbridgeee/is373-ci-cd/milestone/1).

## Ordered work

| Issue | Deliverable | Dependencies | Completion evidence |
| --- | --- | --- | --- |
| [#1 — Docs & GitHub workflow scaffolding](https://github.com/mcbridgeee/is373-ci-cd/issues/1) | Spec, CONTRIBUTING, AGENTS, templates, labels, milestone, this backlog | None | Reviewed links/YAML, pushed directly to `main` |
| [#2 — Environment decisions](https://github.com/mcbridgeee/is373-ci-cd/issues/2) | Host, architecture, Docker Hub repo/visibility, secrets | None | Recorded decisions; no exposed credentials |
| [#3 — Quiz scoring logic + backend tests](https://github.com/mcbridgeee/is373-ci-cd/issues/3) | `quiz.py`, FastAPI routes, unit + integration tests | None | Passing pytest output |
| [#4 — Quiz frontend + browser tests](https://github.com/mcbridgeee/is373-ci-cd/issues/4) | `index.html`, client tally + agreement check, Playwright | #3 | Chromium results and UI review |
| [#5 — Containers & command interface](https://github.com/mcbridgeee/is373-ci-cd/issues/5) | Dockerfile, compose.yaml, Makefile | #2, #3, #4 | Tests against built image, compose verification |
| [#6 — GitHub Actions verify + publish](https://github.com/mcbridgeee/is373-ci-cd/issues/6) | Gated pipeline, Docker Hub publish, branch protection | #5 | Passing/failing runs, registry digest, verified protection |
| [#7 — WUD + rollback](https://github.com/mcbridgeee/is373-ci-cd/issues/7) | Automatic production update, rollback/resume | #2, #5, #6 | Running commit, updater evidence, rollback proof |
| [#14 — Production host decision](https://github.com/mcbridgeee/is373-ci-cd/issues/14) | Droplet at quiz.bmctiernan.com, amd64 only, repo stays private | #2 | Updated architecture/CI docs |
| [#15 — Security policy, Dependabot, labels as code](https://github.com/mcbridgeee/is373-ci-cd/issues/15) | SECURITY.md, security form, dependabot.yml, label sync | None | Sync workflow run, Dependabot config accepted |
| [#16 — Scan the tested image](https://github.com/mcbridgeee/is373-ci-cd/issues/16) | Checksum-pinned Trivy gate on fixable HIGH/CRITICAL | #5, #6 | Scan summary and report artifact |
| [#17 — Harden the HTTP surface](https://github.com/mcbridgeee/is373-ci-cd/issues/17) | Input bounds, CSP and headers, no innerHTML, no prod API docs | #3, #4 | Unit/integration/E2E results |
| [#18 — Public HTTPS at quiz.bmctiernan.com](https://github.com/mcbridgeee/is373-ci-cd/issues/18) | Traefik overlay, droplet deploy runbook | #6, #7, #17 | Public health, headers, unaffected sites |
| [#19 — Daily deployed-image rescan](https://github.com/mcbridgeee/is373-ci-cd/issues/19) | Scheduled scan of the live release | #16, #18 | Manual dispatch run |
| [#8 — Demo rehearsal + evidence docs](https://github.com/mcbridgeee/is373-ci-cd/issues/8) | Full walkthrough, timings, evidence.md | #4, #6, #7, #18 | Recorded end-to-end evidence |

Issue #2 is not a blanket blocker — backend work (#3, #4) can proceed while host/registry decisions are pending.

## Suggested atomic changes

Examples of coherent changes, not a mandated commit count:

1. Add the quiz scoring function with its unit tests.
2. Add HTTP validation, routes, and integration tests.
3. Add the HTML quiz page and browser behavior checks.
4. Add image construction and isolated container test commands.
5. Add CI verification, then publication with its release safeguards.
6. Add updater configuration and prove automatic replacement.
7. Add rollback/resume tooling and the verified demo runbook.

Include tests with the behavior they verify. Reference the issue in commits; close an issue only when all its acceptance criteria are satisfied. Preserve focused commits in PR merges (merge commits, not squash) so history stays atomic.

## Review gates

- **Specification review**: confirm the quiz's question/answer contract and dual-computation rule before application work.
- **Local functionality**: unit, integration, and browser checks prove the intended behavior.
- **Artifact verification**: E2E checks target the built production image.
- **Publication**: only a successful `main` run can promote the tested image.
- **Deployment**: the host's observed commit matches the published release.
- **Demonstration**: a failure blocks release, a fix deploys, rollback/resume work as documented.

## Deferred work

Authentication, a database, quiz history, more than 4 questions, a frontend framework, multiple browser engines, automatic rollback, zero-downtime deployment, GitHub Projects automation. Add only through a new issue with a clear teaching purpose.
