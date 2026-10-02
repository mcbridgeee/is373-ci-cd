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

## Label palette

Labels are color-grouped so the issue list reads at a glance. Pink, turquoise, and white were chosen as the theme; baby blue is deliberately left out so the set never reads as a pink/white/light-blue flag.

| Family | Meaning | Labels |
| --- | --- | --- |
| Pinks | What kind of work it is | `💗 application` (cotton candy), `🚀 ci-cd` (raspberry), `🏠 hosting` (hot pink), `📝 documentation` (blush), `✨ enhancement` (bubblegum) |
| Turquoise | Quality, safety, and testing | `🧪 testing`, `🔒 security`, `📦 dependencies`, `♿ accessibility`, `🌱 good first issue`, `🙋 help wanted` |
| Deep rose / berry | Something is wrong or stuck | `🐛 bug`, `⛔ blocked` |
| White | Parked or closed out | `💭 question`, `👯 duplicate`, `🙅 invalid`, `🌙 wontfix` |

Every label name and description starts with an icon so the meaning is readable even without color. Each issue gets exactly one "kind of work" label, plus `⛔ blocked` or `🐛 bug` when they apply.

### Labels as code (issue 15)

[`.github/labels.json`](../.github/labels.json) is the source of truth. On a push to `main` that changes it, [`labels.yml`](../.github/workflows/labels.yml) runs [`scripts/sync-labels.py`](../scripts/sync-labels.py) with an `issues: write` token. It creates missing labels, fixes colors and descriptions, and renames a label found under one of its `aliases`, so issues keep their labels through a rename. It never deletes a label. To change a label, edit the JSON in a PR rather than the settings page; a settings-page edit is overwritten on the next sync.

## Branch policy

Activate once the `verify` check has passed at least once on a PR (issue 6), so GitHub can offer it as a required check. In **Settings → Rules → Rulesets → New branch ruleset**:

- Name `main`, enforcement **Active**, target **Include default branch**, and leave the bypass list **empty** (no admin bypass, even solo).
- **Restrict deletions** and **Block force pushes**.
- **Require a pull request before merging**, with **0** required approvals (solo maintainer, same as the reference repo). Allowed merge method: **Merge** only, so atomic commits survive.
- **Require status checks to pass**: add `verify` and turn on **Require branches to be up to date before merging**.

After saving, record the date here and link the first PR it applied to.

## Repository settings checklist

Settings that live outside the code, so they can't be reviewed in a PR. Check them once and after any change:

- **Settings → Actions → General → Workflow permissions**: *Read repository contents and packages permissions*; leave *Allow GitHub Actions to create and approve pull requests* off. Workflows that need more ask for it explicitly (`labels.yml` asks for `issues: write`).
- **Settings → Advanced Security** (or **Code security**): turn on **Dependabot alerts** and **Dependabot security updates**. Both work on private repositories.
- **Settings → General → Pull Requests**: allow only **merge commits**; turn on **Automatically delete head branches**.
- **Settings → Secrets and variables → Actions**: only `DOCKER_PAT`. Rotate it on Docker Hub if it is ever printed, and at least once per semester.

Not available while the repository is private: CodeQL code scanning, secret scanning, and push protection. If the repository is made public, turn those on too. Making it public also publishes the email address in existing commit metadata.

## Dependabot (issue 15)

[`.github/dependabot.yml`](../.github/dependabot.yml) opens grouped PRs every Monday for Python packages in `uv.lock`, GitHub Actions SHAs, the Dockerfile's base image digest, and the WUD image in `compose.yaml`. They go through the same `verify` job as any change; merge them like any other PR. A base-image update is how fixed Debian vulnerabilities reach production.

## Security policy (issue 15)

[`SECURITY.md`](../SECURITY.md) sends vulnerability reports away from public issues. The issue chooser links to it. The **Security hardening** form (`security.yml`) is for planning non-sensitive hardening work and asks the author to confirm it contains no secrets.

## Automation and credentials

- Repository secret: `DOCKER_PAT` — a Docker Hub access token for `mcbridgeee`, scoped to push this one repository's image (Read & Write). Set on 2026-09-22 via the GitHub web UI, ahead of issue 6; confirmed present via `gh secret list` (name only), value never printed or committed.
- Non-secret Docker Hub username: `mcbridgeee`. Docker Hub repo `mcbridgeee/is373-ci-cd` created manually as public on 2026-09-22.
- Workflow permissions: `contents: read` at the top of every workflow; a job asks for more only when it needs it.
- Pull requests: verify only, no publishing credentials.
- `main` pushes: verify, then publish the tested image.
- Deployment: WUD on the production droplet (issue 14); no Actions SSH connection or deploy key required.

A GitHub production environment with approval gates is intentionally skipped — this project demonstrates automatic deployment.

## Issue completion and history

Each issue records scope, dependency links, requirements, acceptance criteria, and a validation plan (from the feature form). Close only with evidence, not because a file exists. Reference the issue in atomic commits; close implementation issues through their final PR. Application, CI, and deployment issues stay separate so it's possible to tell code-complete from operationally-complete.

## References

- [GitHub issue form syntax](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms)
- [GitHub repository rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
