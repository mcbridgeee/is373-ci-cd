# CI/CD specification

Status: pipeline implemented in [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) (issue 6); publication is proven only once a `main` run has pushed to Docker Hub. Deployment (issue 7) not yet implemented. Update this line as each stage is actually exercised, with evidence, not just written.

## Pipeline contract

One GitHub Actions job named `verify`, with clearly labeled steps:

1. Check out the exact commit and install pinned test dependencies.
2. Run unit tests (`make test-unit`).
3. Run integration tests (`make test-integration`).
4. Build the production image once, for `linux/amd64`, with commit SHA and UTC build time embedded (`make build`).
5. Start that image in an isolated container and wait for `/health`.
6. Run Chromium E2E tests against it (`make test-e2e`); collect failure evidence and clean up.
7. For a successful `main` push only, authenticate to Docker Hub and publish that same tested image.

Trigger on pull requests and pushes to `main`. A PR run must never receive publishing credentials — no Docker Hub login step runs on `pull_request`. Do not use `pull_request_target` to run contributor code with secrets.

Every stage is a gate: failure before publication leaves the existing `:prod` tag and running production unchanged. Publication is not atomic across two tags — publish the commit tag first, then move `:prod`. An interrupted push can leave an unused commit-tagged image; that's acceptable. The production channel must never point at an untested artifact.

## Tags and publishing

| Tag | Meaning |
| --- | --- |
| `mcbridgeee/is373-ci-cd:sha-<full-commit>` | Release identity; never overwrite an existing commit tag |
| `mcbridgeee/is373-ci-cd:prod` | Most recently promoted release |

Record the published digest in the workflow summary. On rerun, reuse/verify the original artifact rather than silently rebuilding and overwriting its commit tag.

Serialize release workflows with one production concurrency group; do not cancel an in-progress publication. Before promotion, verify the run still represents the current `main` head, so a stale rerun can't move `:prod` backward. A run that finds a newer `main` head stops without moving `:prod` and ends **neutral, not failed**, noting "superseded" in its summary; the newer commit's run publishes instead. (Two quick merges used to leave a red run on `main` for this correct refusal.) PR runs can cancel superseded runs of themselves.

Use the `DOCKER_PAT` Actions secret (a Docker Hub access token) to log in as `mcbridgeee`, through `docker login --password-stdin` in the publish job only, then log out. Least-privilege permissions (`contents: read` unless a step needs more), pin third-party actions to a commit SHA, keep dependency versions reproducible (locked via `pyproject.toml`/lockfile).

## Host-side deployment

[WUD](https://getwud.app/) runs beside `prod` on the production droplet (issue 14) and polls Docker Hub for a changed digest behind `:prod` — digest watching explicitly enabled, candidate tags restricted to `prod` (tag-name comparison alone can't detect replacement of a mutable tag). Opt-in policy only, so `dev`, WUD itself, and unrelated containers are never touched.

WUD polls outward; GitHub needs no inbound access to the droplet, and no self-hosted runner or SSH deploy secret is required. Public traffic reaches `prod` only through the droplet's existing Traefik over HTTPS at `quiz.bmctiernan.com`. The image is public on Docker Hub, so no pull credentials are needed on the host side.

The updater must preserve `prod`'s port, environment, health check, and restart policy, and must never affect `dev`'s container identity.

## Bootstrap sequence

1. Resolve deployment host, architecture, Docker Hub visibility, and credentials — issue 2.
2. Implement and pass local tests — issues 3, 4.
3. Containerize and prove the Make interface — issue 5.
4. Merge the pipeline; publish the first passing release to Docker Hub — issue 6.
5. Start `prod` + `wud` via Compose on the droplet — issue 7.
6. Confirm `/health` and the footer on `:8090` and on `https://quiz.bmctiernan.com` match the published release — issue 18.
7. Publish a second passing change and prove WUD updates `prod` without manual recreation — issue 7.

## Failure and rollback behavior

| Failure | Expected behavior |
| --- | --- |
| Unit/integration/build/E2E | Job fails; no image promotion; previous release stays deployed |
| Registry login or push | Workflow reports failure; do not assume production updated |
| WUD stopped or registry unavailable | Existing production continues; deployment waits |
| New container can't start or is unhealthy | Deployment failed even if publication was green; operator rolls back |

`make rollback RELEASE=<sha-tag-or-digest>`:

1. Pause WUD updates before touching the production image.
2. Select a known-good image by recorded digest or retained commit tag.
3. Pull and recreate **only** `prod`.
4. Check `/health` and verify the previous commit on `:8090`.
5. Leave WUD paused, visibly.

`make resume-updates` restores the `:prod` channel and resumes the updater once the desired release is verified — implemented in `scripts/runtime.py`, matching the reference repo's approach.

The pinned release lives in `.state/release.env` and wins over an exported `PROD_IMAGE`, so a stray shell variable can't undo a rollback. Keep `.state/` across operations. Releases published before #7 don't report `environment` and fail `make verify-production`; roll back only to a release from #7 onward.

### Why release identity is baked into a file

A sandbox run of WUD (issue 7) showed that when it replaces `prod` with a newer image, it **copies the old container's environment variables**. With the commit stored in `ENV BUILD_COMMIT`, the updated container kept reporting the previous commit, so `/health` lied about what was running. The image now writes `app/release.json` at build time and `/health` reads that file, which a recreated container can't inherit. Any other `ENV` set in the Dockerfile is also copied forward by WUD, so release-specific values must never live there.

## Completion evidence

For the deployment issue: record the workflow URL, commit, published digest, WUD update evidence, and the `/health` response from `:8090`. A green publishing run alone is not deployment evidence.
