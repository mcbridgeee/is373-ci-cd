# Security

What protects the quiz, where each control lives, and what is left open. Each control is tied to the issue that added it.

## Controls by layer

| Layer | Control | Where | Issue |
| --- | --- | --- | --- |
| Application | Bounded input, no input echo in errors, text-only rendering, hash-based CSP and browser security headers, no API docs in production | `app/main.py`, `app/index.html`, spec QUIZ-4x | #17 |
| Image | Digest-pinned Debian Trixie base with security updates applied; no pip/setuptools/ensurepip at runtime; UID 10001 over root-owned code | `Dockerfile` | #5 |
| Runtime | Read-only root filesystem, all capabilities dropped, `no-new-privileges`, pids limit, `/tmp` tmpfs `noexec`; ports bound to `127.0.0.1` | `compose.yaml`; E2E runs with the same flags and checks them from inside | #5 |
| Supply chain | Actions pinned to commit SHAs; scanner verified by SHA-256; locked Python deps; Dependabot weekly | `.github/`, `scripts/install-trivy.sh` | #6, #15, #16 |
| Release | PRs never get the Docker Hub token; only the E2E-tested and scanned image of the current `main` head is published; existing `sha-` tags are never overwritten | `.github/workflows/ci.yml`, `scripts/publish.py` | #6, #16 |
| Updater | WUD dashboard requires generated credentials (`.state/wud.env`, mode 600) and listens on loopback only; it watches only `prod` | `compose.yaml`, `scripts/runtime.py` | #7 |
| Public edge | HTTPS only through the droplet's Traefik, HSTS added there | `server-of-love` overlay | #18 |

## Image vulnerability policy (issue 16)

CI scans the exact image ID that passed E2E with Trivy 0.75.0, before it can be saved for publication.

- A **CRITICAL or HIGH finding with a fixed version available fails `verify`**, so the image is never published. Fix it by rebuilding on a patched base (usually a Dependabot base-image PR) or updating the package.
- Findings with **no fixed version** are counted in the job summary and kept as an artifact (`artifacts/security/vulnerabilities.json`). They stay visible; there is no ignore list.
- Scanner errors fail the job.

Run the same check locally with `make build && make scan`.

### Baseline (2026-10-02)

From PR #24's run [37039503038](https://github.com/mcbridgeee/is373-ci-cd/actions/runs/37039503038), image `sha256:255615c1…` (amd64):

| Severity | Findings | Fix available |
| --- | ---: | ---: |
| CRITICAL | 0 | 0 |
| HIGH | 44 | 0 |
| MEDIUM | 60 | 0 |
| LOW | 60 | 0 |
| UNKNOWN | 2 | 0 |

Counts are per package, so one CVE in several binary packages counts more than once. All remaining findings are in Debian base packages with no fix published yet, and none are in Python packages. The same base in the reference repo showed the same set (util-linux, acl, ncurses, systemd, Perl `Archive::Tar`).

The gate does work. A sandbox build that skipped the Dockerfile's `apt-get upgrade` was blocked on 7 fixable findings (OpenSSL CVE-2026-75804 and CVE-2026-84782, PCRE2 CVE-2026-103111). Applying Debian's updates in the base stage is what clears them.

This is a point-in-time result, not proof that the image has no vulnerabilities. New CVEs appear after release, which is why #19 rescans the deployed release daily.

## Daily rescan of the live release (issue 19)

[`deployed-image-security.yml`](../.github/workflows/deployed-image-security.yml) runs daily at 07:17 UTC. It reads the commit from `https://quiz.bmctiernan.com/health`, validates it (status ok, production, 40 hex characters), pulls the immutable `sha-<commit>` tag rather than the moving `prod` tag, and applies the same scanner and policy as CI. A failing run emails the repository owner. That email is the alert to merge the pending Dependabot base-image PR, or to rebuild.

Scheduled runs are off until the site is live. Turn them on with the repository variable `DEPLOYED_SCAN_ENABLED=true` (**Settings → Secrets and variables → Actions → Variables**). **Actions → Deployed image security → Run workflow** runs it on demand at any time.

## Known gaps

- No rate limiting or authentication on the quiz (out of v1 scope).
- WUD mounts the Docker socket, which is effectively root on the droplet. It's kept off the public network and protected by credentials, but anyone with shell access to the droplet can use it.
- CodeQL, secret scanning, and push protection are unavailable while the repository is private (#14).
