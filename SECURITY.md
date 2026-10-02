# Security policy

## Reporting a vulnerability

Please **do not open a public issue, pull request, or discussion** for a vulnerability.

1. Use **Security → Report a vulnerability** on this repository if it is available to you.
2. Otherwise, message [@mcbridgeee](https://github.com/mcbridgeee) on GitHub asking for a private channel. Don't include details until you have one.

Include what is affected (URL, commit from `/health`, or image digest), steps to reproduce, and the impact you observed. Expect a first reply within a week; this is a student teaching project, not a staffed service.

Never send real tokens, passwords, or private keys, even ones you found. Describe where they are instead.

## Supported versions

Only the release currently on the `prod` tag (shown by `https://quiz.bmctiernan.com/health`) gets fixes. Older `sha-` tags exist for rollback and are not patched.

## In scope

- The quiz application in `app/` and its HTTP API
- The container image `mcbridgeee/is373-ci-cd` and its Dockerfile
- The GitHub Actions workflows and release scripts in this repository

## Out of scope

- The droplet's operating system, Traefik, and the other bmctiernan.com sites (tracked in the `server-of-love` repository)
- Vulnerabilities in Debian or Python packages that have no fixed version yet. CI reports them in the image scan (issue 16)
- Denial of service through traffic volume

## What protects this project

- PRs never receive the Docker Hub token. Only a passing push to `main` publishes, and only the exact image that passed testing.
- Workflow tokens are read-only by default and third-party actions are pinned to commit SHAs.
- The image runs as a non-root user with a read-only filesystem, no Linux capabilities, and no way to gain privileges.
- Dependabot proposes dependency, base-image, and action updates weekly.
