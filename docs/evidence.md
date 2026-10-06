# Evidence

Proof behind the claims in the README and [demo.md](demo.md), gathered in one place. Each row links to the run, PR, or issue comment where it happened. "Sandbox" means the authoring environment, which ran the same images and a Traefik configured like the droplet's. The droplet itself is recorded under [Droplet](#droplet) once it's live.

## First release (issue 6)

| | |
| --- | --- |
| Workflow run | [37039222796](https://github.com/mcbridgeee/is373-ci-cd/actions/runs/37039222796): `verify` ✅ → `publish` ✅ |
| Commit | `f5b7319936ffd53554aed7f8bbb183d8c7a2e3d6` |
| Image | `mcbridgeee/is373-ci-cd:sha-f5b7319…` = `:prod` at the time, digest `sha256:c159937793362a6f2085575508383cf2df7566595fe70c8f4ea0303771fb2d2a` |
| Pulled and run | `/health` → `{"status":"ok","commit":"f5b7319936ffd53554aed7f8bbb183d8c7a2e3d6",…}` |

PR runs skip `publish` and never log in to Docker Hub, for example [37038614098](https://github.com/mcbridgeee/is373-ci-cd/actions/runs/37038614098).

## Releases

Every `main` merge that passed `verify` (and wasn't superseded) published a `sha-` tag:

| Tag (commit) | Digest | Published (UTC) | Note |
| --- | --- | --- | --- |
| `sha-f5b7319…` | `sha256:c15993779336…` | 2026-10-02 17:14 | first release |
| `sha-7510b4d…` | `sha256:13f44d55c415…` | 2026-10-02 17:17 | HTTP hardening (#17) |
| `sha-881a0a3…` | `sha256:9c74c6667510…` | 2026-10-02 17:25 | tag pushed, `prod` not moved (superseded) |
| `sha-3cba947…` | `sha256:6f990be40a35…` | 2026-10-02 17:27 | image scan gate (#16) |
| `sha-041c54f…` | `sha256:9e69cd0b67c2…` | 2026-10-02 17:32 | Python base updates (#28) |
| `sha-cb71057…` | `sha256:6b836ea8e4d6…` | 2026-10-02 17:47 | E2E race fix (#31) |
| `sha-cb6124d…` | `sha256:a804090c0e5c…` | 2026-10-02 17:52 | deploy/rollback (#7); first with `environment` |
| `sha-a329d31…` | `sha256:16f7cebe5bba…` | 2026-10-02 17:58 | hosting runbook (#18) |
| `sha-82986cf…` | `sha256:c0583268afaf…` | 2026-10-02 18:05 | daily rescan (#19) |
| `sha-995f5c5…` | `sha256:c76b7af7029f…` | 2026-10-02 18:07 | status docs |
| `sha-0de9167…` | `sha256:96ba8a347b8c…` | 2026-10-05 16:55 | FastAPI 0.142.2 (Dependabot #36) |
| `sha-be5c23c…` | `sha256:ef461cf784ae…` | 2026-10-05 17:06 | WUD 9.2.1 (Dependabot #35) |

Rollback targets: releases from `cb6124d` onward. Earlier ones don't report `environment`, so `make verify-production` rightly refuses them.

## Blocked changes (issue 37)

| PR | Fault | Run | Failing step | Earlier steps | `publish` |
| --- | --- | --- | --- | --- | --- |
| [#38](https://github.com/mcbridgeee/is373-ci-cd/pull/38) | recommends Colgate | [37344513851](https://github.com/mcbridgeee/is373-ci-cd/actions/runs/37344513851) | Unit tests | n/a | skipped |
| [#39](https://github.com/mcbridgeee/is373-ci-cd/pull/39) | API field renamed | [37344522155](https://github.com/mcbridgeee/is373-ci-cd/actions/runs/37344522155) | Integration tests | unit ✅ | skipped |
| [#40](https://github.com/mcbridgeee/is373-ci-cd/pull/40) | submit handler removed | [37344531464](https://github.com/mcbridgeee/is373-ci-cd/actions/runs/37344531464) | E2E tests against the release image | unit ✅ integration ✅ build ✅ | skipped |

All three were closed unmerged. During them `prod` moved only for the unrelated `main` release `sha-0de9167…`.

## Image security (issue 16)

Baseline scan ([37039503038](https://github.com/mcbridgeee/is373-ci-cd/actions/runs/37039503038)): 0 CRITICAL; 44 HIGH, 60 MEDIUM, 60 LOW, 2 UNKNOWN, **0 with a fix available**. Details and policy in [security.md](security.md). The gate was proven to block: a sandbox image built without Debian's updates failed on 7 fixable OpenSSL/PCRE2 findings.

## Updates, rollback, resume (issue 7, sandbox)

Full table in the [#7 comment](https://github.com/mcbridgeee/is373-ci-cd/issues/7#issuecomment-5958281023). In short, through the public-style route `https://quiz.bmctiernan.com` behind Traefik:

| Step | Result |
| --- | --- |
| Deploy `cb6124d` | verified: image ID matches, `environment: production` |
| Merge → CI publishes `a329d31` | WUD replaced `prod` on its own about 90 s later; public `/health` showed `a329d31` |
| `make rollback RELEASE=sha-cb6124d…` | 14.5 s, WUD paused, public `/health` `cb6124d`; an exported `PROD_IMAGE` couldn't override it |
| `make resume-updates` | back on `prod` (`a329d31`), WUD running |

## Problems found by testing for real

| Found | Fix |
| --- | --- |
| WUD copies the old container's env vars, so `/health` reported the **old** commit after an update | release identity baked into `app/release.json` in the image (#27) |
| Dependabot's Python 3.14 image kept `ensurepip` (hard-coded 3.13 path); the in-container check failed CI | version-independent removal; Dependabot limited to patches (#28, #29) |
| Two quick merges left a red run although the guard worked correctly | superseded publishes end neutral (#30) |
| Browser tests answered before the questions loaded (race) | wait for all 4 questions (#31) |
| Docker Hub `429` rate limit when polling every minute | WUD polls every 5 minutes (#32) |

## Server hardening (server-of-love #2, sandbox)

[server-of-love PR #4](https://github.com/mcbridgeee/server-of-love/pull/4): a 600-request flood got 303 `429`s while 90 simultaneous classroom-style requests all got `200`. fail2ban matched all 303 rate-limited log lines and none of the normal ones, then banned the flooding IP, and a banned outside client was refused at the firewall while others were served. Dashboard: no or wrong password `401`, correct `200`.

## Droplet

Deployed 2026-10-06 on the droplet (Ubuntu 24.04.5, x86_64) as `bridge`, following [hosting.md](hosting.md) (#18):

- [x] `sudo make deploy`: `Verified production: mcbridgeee/is373-ci-cd:prod`, commit `4847d195974aeb71e6d87822fcb1ca0f603376d6`, `environment: production`, then WUD started
- [x] `sudo make status`: `prod` healthy on `127.0.0.1:8090`, `wud` on `127.0.0.1:8091`, `Updates: enabled`
- [x] from outside: `https://quiz.bmctiernan.com/health` and `https://calc.bmctiernan.com/health` both `environment: production`, commit `4847d19`; `http://quiz.bmctiernan.com` → `301` to https; Content-Security-Policy present
- [x] the other sites still `200`: `bmctiernan.com`, `www.bmctiernan.com`, `report.bmctiernan.com`
- [ ] a WUD update on the droplet (commit before → after): the merge of this page is the first one
- [ ] a rollback → resume cycle on the droplet
- [ ] server hardening applied: `sudo ~/server-of-love/security/check.sh` all PASS (server-of-love #2)
- [ ] first `Deployed image security` run against the live site
