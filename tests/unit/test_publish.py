"""Release guards in scripts/publish.py: only the tested image for current main publishes."""

import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("publish", Path(__file__).parents[2] / "scripts" / "publish.py")
publish = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publish)

COMMIT = "a" * 40
IMAGE_ID = "sha256:" + "b" * 64


def image(**overrides):
    base = {
        "Id": IMAGE_ID,
        "Os": "linux",
        "Architecture": "amd64",
        "Config": {"Labels": {"org.opencontainers.image.revision": COMMIT}},
    }
    return {**base, **overrides}


def test_current_main_push_is_publishable():
    publish.validate_release("push", "refs/heads/main", COMMIT, COMMIT)


@pytest.mark.parametrize(
    "event, ref, head",
    [
        ("pull_request", "refs/heads/main", COMMIT),
        ("workflow_dispatch", "refs/heads/main", COMMIT),
        ("push", "refs/heads/feature", COMMIT),
    ],
)
def test_prs_manual_runs_and_other_branches_are_refused(event, ref, head):
    with pytest.raises(ValueError):
        publish.validate_release(event, ref, COMMIT, head)


def test_older_main_commit_is_superseded_not_failed():
    # Two quick merges: the older run must not move prod, and must not go red.
    with pytest.raises(publish.Superseded):
        publish.validate_release("push", "refs/heads/main", COMMIT, "c" * 40)
    assert not issubclass(publish.Superseded, ValueError)


def test_short_sha_is_refused():
    with pytest.raises(ValueError):
        publish.validate_release("push", "refs/heads/main", "abc1234", "abc1234")


def test_tested_image_is_publishable():
    publish.validate_artifact({"commit": COMMIT, "image_id": IMAGE_ID}, image(), COMMIT)


@pytest.mark.parametrize(
    "tested, loaded",
    [
        ({"commit": "c" * 40, "image_id": IMAGE_ID}, image()),
        ({"commit": COMMIT, "image_id": IMAGE_ID}, image(Id="sha256:" + "d" * 64)),
        ({"commit": COMMIT, "image_id": IMAGE_ID}, image(Architecture="arm64")),
        ({"commit": COMMIT, "image_id": IMAGE_ID}, image(Config={"Labels": {}})),
    ],
)
def test_untested_or_mismatched_images_are_refused(tested, loaded):
    with pytest.raises(ValueError):
        publish.validate_artifact(tested, loaded, COMMIT)
