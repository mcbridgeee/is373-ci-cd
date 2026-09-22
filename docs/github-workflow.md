# GitHub workflow and configuration

## Initial repository setup (issue 1)

The documentation phase adds:

- An implementation task form with requirements and acceptance criteria (`.github/ISSUE_TEMPLATE/feature.yml`).
- A bug form with environment/release and reproduction evidence (`bug.yml`).
- A specification decision form for open questions (`decision.yml`).
- A PR template linking the issue, specification, and validation.
- A v1 milestone and 8 ordered implementation issues.
- Labels `application`, `testing`, `ci-cd`, `blocked`, alongside GitHub's standard labels.
- Focused documentation commits pushed directly to `main` for review (this repo has no history to protect yet).

Blank issues remain enabled so the forms don't block unusual reports. Issues track development units; the milestone tracks the complete demo. No Project board — the backlog is small enough that one isn't worth the overhead.

## Branch policy

Not yet enabled. Plan (to activate once issue 6 has a first passing `verify` run on a PR, per the reference repo's sequencing):

- Require a PR into `main`.
- Require the `verify` check to be passing and up to date.
- Block force pushes and branch deletion on `main`.
- Enforce for administrators too (no bypass, even solo).
- **Zero required reviewer approvals** — this is a solo-maintainer teaching repo, same as the reference.

## Automation and credentials

- Repository secret: `DOCKER_PAT` — a Docker Hub access token for `mcbridgeee`, scoped to push this one repository's image (Read & Write). Set on 2026-09-22 via the GitHub web UI, ahead of issue 6; confirmed present via `gh secret list` (name only), value never printed or committed.
- Non-secret Docker Hub username: `mcbridgeee`. Docker Hub repo `mcbridgeee/is373-ci-cd` created manually as public on 2026-09-22.
- Workflow permissions: start with `contents: read`.
- Pull requests: verify only, no publishing credentials.
- `main` pushes: verify, then publish the tested image.
- Deployment: WUD on this host; no Actions SSH connection required.

A GitHub production environment with approval gates is intentionally skipped — this project demonstrates automatic deployment.

## Issue completion and history

Each issue records scope, dependency links, requirements, acceptance criteria, and a validation plan (from the feature form). Close only with evidence, not because a file exists. Reference the issue in atomic commits; close implementation issues through their final PR. Application, CI, and deployment issues stay separate so it's possible to tell code-complete from operationally-complete.

## References

- [GitHub issue form syntax](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms)
- [GitHub repository rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
