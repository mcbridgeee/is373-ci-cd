"""Make the repository's labels match .github/labels.json.

Creates missing labels, updates colors and descriptions, and renames a label
found under one of its aliases (renaming keeps it on every issue). Labels not
in the file are left alone, so nothing is ever deleted.

Run by .github/workflows/labels.yml with GH_TOKEN; needs only issues: write.
"""

import json
import os
from pathlib import Path
import re
import subprocess
import urllib.parse

ROOT = Path(__file__).resolve().parents[1]


def load(path=ROOT / ".github" / "labels.json"):
    labels = json.loads(Path(path).read_text())["labels"]
    names = set()
    for label in labels:
        if not re.fullmatch(r"[0-9a-f]{6}", label["color"]):
            raise ValueError(f"{label['name']}: color must be 6 lowercase hex digits")
        if len(label["description"]) > 100:
            raise ValueError(f"{label['name']}: GitHub limits descriptions to 100 characters")
        for name in [label["name"], *label.get("aliases", [])]:
            if name in names:
                raise ValueError(f"{name} appears more than once")
            names.add(name)
    return labels


def plan(labels, existing):
    """Return (method, current_name_or_None, fields) actions to apply."""
    actions = []
    for label in labels:
        fields = {"color": label["color"], "description": label["description"]}
        if label["name"] in existing:
            current = existing[label["name"]]
            if (current["color"], current.get("description") or "") != (fields["color"], fields["description"]):
                actions.append(("PATCH", label["name"], fields))
            continue
        alias = next((a for a in label.get("aliases", []) if a in existing), None)
        if alias:
            actions.append(("PATCH", alias, {**fields, "new_name": label["name"]}))
        else:
            actions.append(("POST", None, {**fields, "name": label["name"]}))
    return actions


def gh(*args):
    return subprocess.run(["gh", "api", *args], check=True, capture_output=True, text=True).stdout


def main():
    repo = os.environ["GITHUB_REPOSITORY"]
    pages = gh("--paginate", "--slurp", f"repos/{repo}/labels")
    existing = {label["name"]: label for page in json.loads(pages) for label in page}
    actions = plan(load(), existing)
    for method, current, fields in actions:
        path = f"repos/{repo}/labels" + (f"/{urllib.parse.quote(current, safe='')}" if current else "")
        args = [f"--method={method}", path]
        for key, value in fields.items():
            args += ["-f", f"{key}={value}"]
        gh(*args)
        print(f"{method} {current or fields['name']} -> {fields.get('new_name', fields.get('name', current))}")
    print(f"{len(actions)} change(s) applied; labels match .github/labels.json")


if __name__ == "__main__":
    main()
