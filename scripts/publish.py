"""Publish the exact image that passed CI, then move the prod channel to it.

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


def output(args):
    return subprocess.check_output(args, text=True).strip()


def validate_release(event, ref, commit, main_head):
    """Only the current head of main, from a push, may be published."""
    if event != "push" or ref != "refs/heads/main":
        raise ValueError("Publication requires a main push, never a PR or manual run")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("A full commit SHA is required")
    if commit != main_head:
        raise ValueError("Refusing to promote a stale main commit")


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


def main():
    commit = os.environ["GITHUB_SHA"]
    folder = Path(os.getenv("RELEASE_DIR", "release-artifact"))
    tested = json.loads((folder / "tested-image.json").read_text())
    subprocess.run(["docker", "load", "-i", str(folder / "image.tar")], check=True)
    image = json.loads(output(["docker", "image", "inspect", tested["image_id"]]))[0]
    validate_artifact(tested, image, commit)

    def check_current():
        head = output(["gh", "api", f"repos/{os.environ['GITHUB_REPOSITORY']}/git/ref/heads/main", "--jq", ".object.sha"])
        validate_release(os.environ["GITHUB_EVENT_NAME"], os.environ["GITHUB_REF"], commit, head)

    check_current()
    version_tag = f"sha-{commit}"
    if tag_exists(version_tag):
        raise SystemExit(f"{version_tag} already exists. Refusing to overwrite a release; push a new commit instead.")

    version = f"{REPOSITORY}:{version_tag}"
    subprocess.run(["docker", "tag", tested["image_id"], version], check=True)
    subprocess.run(["docker", "push", version], check=True)
    details = json.loads(output(["docker", "image", "inspect", version]))[0]
    digest = next(d for d in details["RepoDigests"] if d.startswith(REPOSITORY + "@"))

    # Re-check right before moving prod so a slow run can't move it backward.
    check_current()
    channel = f"{REPOSITORY}:prod"
    subprocess.run(["docker", "tag", tested["image_id"], channel], check=True)
    subprocess.run(["docker", "push", channel], check=True)

    with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as summary:
        summary.write(
            "## Published release\n\n"
            f"- Commit: `{commit}`\n- Version: `{version}`\n- Channel: `{channel}`\n- Digest: `{digest}`\n\n"
            "This image passed E2E before publication. Check the running `/health` commit separately.\n"
        )
    print(json.dumps({"commit": commit, "version": version, "digest": digest}, indent=2))


if __name__ == "__main__":
    main()
