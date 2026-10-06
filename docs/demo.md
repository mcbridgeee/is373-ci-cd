# Demo script

What to show when the instructor comes around. It follows the same order as the reference repo's [demo runbook](https://github.com/kaw393939/is373_ci_cd/blob/main/docs/demo.md): test levels, a live release, blocked changes, rollback. Each part takes a minute or two. Proof for every claim is in [evidence.md](evidence.md).

## The instructor's requirements, and how to show each

| # | Requirement | Where it lives | Show it |
| --- | --- | --- | --- |
| 1 | fail2ban blocks people after repeated failed attempts | server-of-love `security/fail2ban/` | `sudo fail2ban-client status sshd` (bots get banned all day) and `sudo fail2ban-client status traefik-quiz-ratelimit` |
| 2 | Security updates every night at 2am | server-of-love `security/updates/`, timer drop-ins | `systemctl list-timers 'apt-daily*'` shows tonight 01:30 and 02:00; `sudo tail /var/log/unattended-upgrades/unattended-upgrades.log` after the first night |
| 3 | No root login over SSH | server-of-love `security/ssh/10-server-of-love.conf` | `sudo sshd -T \| grep permitrootlogin` → `no`; `ssh root@<droplet-ip>` → `Permission denied (publickey)` |
| 4 | Trivy in the GitHub Action that deploys the image | `.github/workflows/ci.yml`, `scripts/scan-image.py` (#16) | any `verify` run → "Scan the exact tested image" step and the severity table in its summary |
| 4 | Hardened Dockerfile | `Dockerfile` (#5) | the file (digest-pinned base, security updates, no pip, non-root UID 10001) and the E2E step's "Container hardening checks passed" |
| 5 | Push to deploy: GitHub → Docker Hub → server updates itself | `ci.yml` publish job, WUD in `compose.yaml` (#6, #7, #18) | step 3 below: merge a PR, then watch the live site's footer commit change |

Fastest proof of the server items: `sudo ~/server-of-love/security/check.sh` on the droplet prints PASS/FAIL for fail2ban, 2am updates, root and password SSH login, firewall and open ports, the dashboard login, and the live quiz. It changes nothing and prints no secrets.

Server steps: [server-of-love security/README.md](https://github.com/mcbridgeee/server-of-love/blob/main/security/README.md). App deploy on the droplet: [hosting.md](hosting.md).

## Before class (10 minutes)

Pick where production runs:

| | Droplet (best) | Laptop (fallback) |
| --- | --- | --- |
| Production URL | `https://quiz.bmctiernan.com` | `http://localhost:8090` |
| Set up with | [hosting.md](hosting.md) | `make setup && make browsers && make up` |
| Run commands | over SSH in `~/is373-ci-cd`, with `sudo` | in the repo folder on your laptop |

Then:

1. `make status`: production is running, `Updates: enabled`.
2. Open these tabs: the quiz, [Actions](https://github.com/mcbridgeee/is373-ci-cd/actions), [Pull requests (closed)](https://github.com/mcbridgeee/is373-ci-cd/pulls?q=is%3Apr+is%3Aclosed), [Issues](https://github.com/mcbridgeee/is373-ci-cd/issues), and [Docker Hub tags](https://hub.docker.com/r/mcbridgeee/is373-ci-cd/tags).
3. Note the current production commit: `curl -s <production URL>/health`.

## 1. The project history (30 seconds)

- **Issues** with icon labels, one per piece of work, on one milestone.
- **Commits** reference their issue, `feat: … (#17)`, and PRs merge with merge commits so each step stays visible: `git log --oneline --graph | head -30`.
- PR template, issue forms (including a security one), `SECURITY.md`, Dependabot.

## 2. Three test levels (1 minute)

Take the quiz in the browser: pick answers, submit, and see **Sensodyne** plus the agreement box. Point at the footer: it shows the exact commit that's running.

```sh
make test-unit          # quiz.py rules, plain Python
make test-integration   # the real FastAPI routes, in-process
make build              # the release image, built once
make test-e2e           # Chromium against that image, run with production's restrictions
```

What each level catches that the one below can't: unit checks the scoring rule; integration checks the HTTP contract; E2E checks the real page in a real browser against the real container.

## 3. A live release (3–5 minutes)

1. Open an issue ("Change the quiz subtitle"), then a branch `feat/<issue>-subtitle`.
2. Edit the `<p>` under the `<h1>` in `app/index.html`. With `make dev` running you see it on `localhost:8080`; production doesn't change.
3. Commit with `(#<issue>)`, push, open a PR with the template.
4. In Actions, watch `verify`: unit → integration → build → E2E → **vulnerability scan**. `publish` is **skipped** on PRs: they never get the Docker Hub password.
5. Merge. The `main` run publishes **the exact image that was tested** as `sha-<commit>` and moves `prod`. Its summary shows the digest.
6. Run `make check-updates` (WUD would otherwise check within 5 minutes), then refresh the quiz. The new subtitle and the new footer commit appear.

Say it out loud: a green publish isn't proof of deployment. The proof is `/health` on the running site showing the new commit.

## 4. Blocked changes (1 minute)

Three deliberately broken PRs, closed and never merged (#37):

| PR | What's broken | Where CI stopped | Published? |
| --- | --- | --- | --- |
| [#38](https://github.com/mcbridgeee/is373-ci-cd/pull/38) | Recommends Colgate | **Unit tests** | No |
| [#39](https://github.com/mcbridgeee/is373-ci-cd/pull/39) | API renames `server_result` | **Integration tests** (unit passed) | No |
| [#40](https://github.com/mcbridgeee/is373-ci-cd/pull/40) | Submit button disconnected | **E2E tests** (unit, integration, build passed) | No |

Point at #40: only a browser test can catch a page that's wired wrong.

## 5. Security (1 minute, if asked)

- **Image:** non-root user, read-only filesystem, no Linux capabilities, no pip. The E2E step checks all of that from inside the container.
- **Scan:** every image is scanned before publishing; a fixable HIGH/CRITICAL blocks it. Open any `verify` run's summary for the table.
- **App:** `curl -s -D - -o /dev/null <production URL>/` shows the Content-Security-Policy and other headers; `/docs` is 404 in production.
- **Server** (droplet only): HTTPS with HSTS, rate limiting, fail2ban. See [server-of-love security/README.md](https://github.com/mcbridgeee/server-of-love/blob/main/security/README.md) for the safe way to show a ban **without flooding from the classroom**, which would ban everyone's shared IP.

## 6. Roll back and resume (2 minutes)

```sh
make rollback RELEASE=sha-995f5c576072c25143984e34148bdd878392c8f8
make status                 # Updates: paused, and the older commit in /health
```

Refresh the quiz: the footer shows `995f5c5`. WUD is stopped, so nothing undoes the rollback.

```sh
make resume-updates         # back to the prod tag, verified, WUD running again
make status
```

Roll back only to releases from #7 onward (they report `environment`); every `sha-` tag in [evidence.md](evidence.md#releases) qualifies.

## Likely questions

| Question | Short answer |
| --- | --- |
| Why build once? | So the image in production is byte-for-byte the one the tests passed. Publish loads the saved tested image; it never rebuilds |
| How does the server get updates without SSH from GitHub? | WUD on the server polls Docker Hub for a new `prod` digest and recreates only the quiz container |
| What if two PRs merge back to back? | The older run sees `main` moved and stops without touching `prod` ("superseded", neutral, not red) |
| What's a digest? | The hash of the exact image contents. Tags can move; a digest can't |
| What did testing catch? | WUD copying the old container's environment so `/health` lied about the version (#7), installers left in a Python 3.14 image (#28), a race in the browser tests (#31) |

## If you change the quiz

Go ahead. Use the release flow in step 3. The tests and [spec.md](spec.md) assume exactly 4 questions with 4 choices and that the answer is always "Sensodyne". If you change those rules, update `docs/spec.md`, `tests/unit/test_quiz.py`, `tests/integration/test_api.py`, and `QUESTION_COUNT` in `tests/e2e/test_quiz.py` in the same PR, or CI blocks it (which is the point).
