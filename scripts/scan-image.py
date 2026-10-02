"""Scan a local Docker image with the pinned Trivy and enforce the release policy.

Policy (docs/security.md): a CRITICAL or HIGH finding that has a fixed version
available blocks the release. Unfixed findings are reported, never hidden.
Scanner errors fail the job.

Usage: python3 scripts/scan-image.py IMAGE OUTPUT_DIR
"""

import collections
import json
import os
from pathlib import Path
import subprocess
import sys

SEVERITIES = ("CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN")
BLOCKING = {"CRITICAL", "HIGH"}
TRIVY = os.getenv("TRIVY", ".tools/trivy/trivy")


def findings(report):
    for result in report.get("Results") or []:
        for vulnerability in result.get("Vulnerabilities") or []:
            yield result.get("Target", ""), vulnerability


def summarize(report):
    """Severity -> (total, fixable) counts."""
    totals, fixable = collections.Counter(), collections.Counter()
    for _target, vulnerability in findings(report):
        severity = vulnerability.get("Severity", "UNKNOWN")
        totals[severity] += 1
        if vulnerability.get("FixedVersion"):
            fixable[severity] += 1
    return {severity: (totals[severity], fixable[severity]) for severity in SEVERITIES}


def blocking(report):
    """Findings that fail the release: CRITICAL/HIGH with a fix available."""
    return [
        (target, v["VulnerabilityID"], v.get("PkgName", ""), v.get("InstalledVersion", ""), v["FixedVersion"])
        for target, v in findings(report)
        if v.get("Severity") in BLOCKING and v.get("FixedVersion")
    ]


def main():
    image, output = sys.argv[1:]
    directory = Path(output)
    directory.mkdir(parents=True, exist_ok=True)
    metadata = json.loads(subprocess.check_output(["docker", "image", "inspect", image]))[0]
    identity = {
        "image_id": metadata["Id"],
        "architecture": metadata["Architecture"],
        "commit": (metadata["Config"].get("Labels") or {}).get("org.opencontainers.image.revision"),
        "policy": "fail on fixable CRITICAL/HIGH; report everything else",
    }
    (directory / "image-identity.json").write_text(json.dumps(identity, indent=2) + "\n")

    report_path = directory / "vulnerabilities.json"
    subprocess.run([
        TRIVY, "image", "--quiet", "--scanners", "vuln", "--format", "json", "--output", str(report_path),
        "--exit-code", "0", "--timeout", "10m", "--image-src", "docker", metadata["Id"],
    ], check=True)
    report = json.loads(report_path.read_text())
    counts = summarize(report)
    blockers = blocking(report)

    lines = [
        "### Image vulnerability scan",
        f"Image `{identity['image_id']}` ({identity['architecture']}), commit `{identity['commit']}`",
        "",
        "| Severity | Findings | Fix available |",
        "| --- | ---: | ---: |",
        *[f"| {severity} | {total} | {fixable} |" for severity, (total, fixable) in counts.items()],
        "",
    ]
    if blockers:
        lines += ["**Blocking (fixable CRITICAL/HIGH):**", ""]
        lines += [f"- `{cve}` in `{pkg}` {installed} → {fixed} ({target})" for target, cve, pkg, installed, fixed in blockers]
        lines.append("")
    summary = "\n".join(lines)
    (directory / "summary.md").write_text(summary)
    print(summary)
    if path := os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(path, "a") as stream:
            stream.write(summary + "\n")
    if blockers:
        raise SystemExit(f"{len(blockers)} fixable CRITICAL/HIGH finding(s). Rebuild on a patched base or update the package.")


if __name__ == "__main__":
    main()
