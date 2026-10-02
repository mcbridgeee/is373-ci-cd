"""Label file validity and the rename-not-recreate rule in scripts/sync-labels.py."""

import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("sync_labels", Path(__file__).parents[2] / "scripts" / "sync-labels.py")
sync_labels = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync_labels)

LABEL = {"name": "🐛 bug", "color": "e11d48", "description": "🐛 Something isn't working", "aliases": ["bug"]}


def test_repository_label_file_is_valid():
    labels = sync_labels.load()
    assert labels and all(not label["name"][0].isascii() for label in labels), "every label starts with its icon"


def test_old_name_is_renamed_so_issues_keep_the_label():
    existing = {"bug": {"name": "bug", "color": "d73a4a", "description": "old"}}
    [(method, current, fields)] = sync_labels.plan([LABEL], existing)
    assert (method, current, fields["new_name"]) == ("PATCH", "bug", "🐛 bug")


def test_missing_label_is_created():
    [(method, current, fields)] = sync_labels.plan([LABEL], {})
    assert (method, current, fields["name"]) == ("POST", None, "🐛 bug")


def test_matching_label_needs_no_change():
    existing = {"🐛 bug": {k: LABEL[k] for k in ("name", "color", "description")}}
    assert sync_labels.plan([LABEL], existing) == []


def test_duplicate_names_are_rejected(tmp_path):
    path = tmp_path / "labels.json"
    path.write_text('{"labels": [%s, %s]}' % (
        '{"name": "a", "color": "ffffff", "description": ""}',
        '{"name": "b", "color": "ffffff", "description": "", "aliases": ["a"]}',
    ))
    with pytest.raises(ValueError):
        sync_labels.load(path)
