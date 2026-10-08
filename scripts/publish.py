"""Publish the exact image that passed CI, then move its channel to it.

Promotion rule: a push to `qa` moves the `qa` channel (qa.bmctiernan.com);
a push to `main` moves the `prod` channel (bmctiernan.com).

Runs only in the publish job of .github/workflows/ci.yml. Nothing is rebuilt:
the image comes from `docker load` of the artifact the verify job saved.
"""

import json
import os
from pathlib import Path
import re
import subprocess
import urllib.error
import urllib.request

REPOSITORY = "mcbridgeee/is373-ci-cd"

# Branch -> (channel tag, prefix for the immutable version tag). QA uses its own
# prefix so promoting the same commit to main never collides with a QA tag.
CHANNELS = {
    "refs/heads/main": ("prod", "sha-"),
    "refs/heads/qa": ("qa", "qa-sha-"),
}


def output(args):
    return subprocess.check_output(args, text=True).strip()


class Superseded(Exception):
    """A newer commit is on the branch; its own run publishes instead. Not a failure."""


def validate_release(event, ref, commit, branch_head):
    """Only the current head of main or qa, from a push, may be published."""
    if event != "push" or ref not in CHANNELS:
        raise ValueError("Publication requires a main or qa push, never a PR or manual run")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("A full commit SHA is required")
    if commit != branch_head:
        raise Superseded(f"{ref} is now {branch_head}; not promoting older {commit}")
    return CHANNELS[ref]


def validate_artifact(tested, image, commit):
    """The loaded image must be the one E2E tested, for this commit and platform."""
    if tested.get("commit") != commit:
        raise ValueError("Test evidence is for a different commit")
    if image.get("Id") != tested.get("image_id"):
        raise ValueError("Loaded image is not the E2E-tested image")
    if (image.get("Os"), image.get("Architecture")) != ("linux", "amd64"):
        raise ValueError("Loaded image is not linux/amd64")
    labels = image.get("Config", {}).get("Labels") or {}
    if labels.get("org.opencontainers.image.revision") != commit:
        raise ValueError("Image release label does not match the commit")


def tag_exists(tag):
    try:
        with urllib.request.urlopen(f"https://hub.docker.com/v2/repositories/{REPOSITORY}/tags/{tag}/", timeout=20):
            return True
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return False
        raise  # A network or auth failure is not evidence that the tag is absent.


def summarize(text):
    print(text)
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as summary:
        summary.write(text + "\n")


def main():
    try:
        publish()
    except Superseded as reason:
        # Safe: prod is untouched (a sha- tag may exist, unused). Neutral, not red.
        summarize(f"## Not promoted: superseded\n\n{reason}. The newer commit's run publishes instead.")


def publish():
    commit = os.environ["GITHUB_SHA"]
    folder = Path(os.getenv("RELEASE_DIR", "release-artifact"))
    tested = json.loads((folder / "tested-image.json").read_text())
    subprocess.run(["docker", "load", "-i", str(folder / "image.tar")], check=True)
    image = json.loads(output(["docker", "image", "inspect", tested["image_id"]]))[0]
    validate_artifact(tested, image, commit)

    ref = os.environ["GITHUB_REF"]

    def check_current():
        branch = ref.removeprefix("refs/")
        head = output(["gh", "api", f"repos/{os.environ['GITHUB_REPOSITORY']}/git/ref/{branch}", "--jq", ".object.sha"])
        return validate_release(os.environ["GITHUB_EVENT_NAME"], ref, commit, head)

    channel_tag, prefix = check_current()
    version_tag = f"{prefix}{commit}"
    if tag_exists(version_tag):
        raise SystemExit(f"{version_tag} already exists. Refusing to overwrite a release; push a new commit instead.")

    version = f"{REPOSITORY}:{version_tag}"
    subprocess.run(["docker", "tag", tested["image_id"], version], check=True)
    subprocess.run(["docker", "push", version], check=True)
    details = json.loads(output(["docker", "image", "inspect", version]))[0]
    digest = next(d for d in details["RepoDigests"] if d.startswith(REPOSITORY + "@"))

    # Re-check right before moving the channel so a slow run can't move it backward.
    check_current()
    channel = f"{REPOSITORY}:{channel_tag}"
    subprocess.run(["docker", "tag", tested["image_id"], channel], check=True)
    subprocess.run(["docker", "push", channel], check=True)

    summarize(
        "## Published release\n\n"
        f"- Commit: `{commit}`\n- Version: `{version}`\n- Channel: `{channel}`\n- Digest: `{digest}`\n\n"
        "This image passed E2E before publication. Check the running `/health` commit separately."
    )


if __name__ == "__main__":
    main()
