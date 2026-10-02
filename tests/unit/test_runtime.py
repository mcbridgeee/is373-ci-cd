"""Release selection rules in scripts/runtime.py."""

import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("runtime", Path(__file__).parents[2] / "scripts" / "runtime.py")
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)

COMMIT = "f" * 40
DIGEST = "sha256:" + "e" * 64


def test_commit_and_digest_releases_become_registry_references():
    assert runtime.release_reference(f"sha-{COMMIT}") == f"mcbridgeee/is373-ci-cd:sha-{COMMIT}"
    assert runtime.release_reference(DIGEST) == f"mcbridgeee/is373-ci-cd@{DIGEST}"


@pytest.mark.parametrize("release", ["", "prod", "latest", "sha-abc1234", f"sha-{COMMIT}; rm -rf /", "sha256:abc"])
def test_anything_else_is_refused(release):
    with pytest.raises(ValueError):
        runtime.release_reference(release)


def test_persisted_rollback_beats_an_exported_prod_image(tmp_path):
    (tmp_path / "release.env").write_text(f"PROD_IMAGE=mcbridgeee/is373-ci-cd:sha-{COMMIT}\n")
    environment = runtime.compose_environment({"PROD_IMAGE": "something:else"}, tmp_path)
    assert environment["PROD_IMAGE"] == f"mcbridgeee/is373-ci-cd:sha-{COMMIT}"


def test_without_a_selection_the_shell_value_is_kept(tmp_path):
    assert runtime.compose_environment({"PROD_IMAGE": "x:y"}, tmp_path)["PROD_IMAGE"] == "x:y"
