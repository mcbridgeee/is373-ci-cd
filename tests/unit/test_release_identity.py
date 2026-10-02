"""Release identity comes from the baked file, not the (copyable) environment."""

import json

from app.main import release_identity


def test_baked_release_file_wins_over_stale_environment(tmp_path, monkeypatch):
    # WUD recreates prod with the previous container's environment.
    monkeypatch.setenv("BUILD_COMMIT", "old" * 13 + "d")
    release = tmp_path / "release.json"
    release.write_text(json.dumps({"commit": "a" * 40, "built_at": "2026-10-02T00:00:00Z"}))
    assert release_identity(release)["commit"] == "a" * 40


def test_environment_is_used_only_when_no_file_was_baked(tmp_path, monkeypatch):
    monkeypatch.setenv("BUILD_COMMIT", "dev")
    assert release_identity(tmp_path / "missing.json")["commit"] == "dev"
