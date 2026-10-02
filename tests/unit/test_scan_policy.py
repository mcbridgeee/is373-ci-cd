"""Release policy in scripts/scan-image.py: only fixable CRITICAL/HIGH findings block."""

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("scan_image", Path(__file__).parents[2] / "scripts" / "scan-image.py")
scan_image = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scan_image)


def vuln(severity, fixed=""):
    return {"VulnerabilityID": f"CVE-{severity}-{fixed or 'none'}", "Severity": severity,
            "PkgName": "pkg", "InstalledVersion": "1", "FixedVersion": fixed}


REPORT = {"Results": [
    {"Target": "debian", "Vulnerabilities": [vuln("CRITICAL", "2"), vuln("HIGH"), vuln("MEDIUM", "3")]},
    {"Target": "python", "Vulnerabilities": None},
]}


def test_only_fixable_critical_and_high_findings_block():
    assert [b[1] for b in scan_image.blocking(REPORT)] == ["CVE-CRITICAL-2"]


def test_unfixed_high_and_fixable_medium_are_reported_not_blocking():
    counts = scan_image.summarize(REPORT)
    assert counts["HIGH"] == (1, 0)
    assert counts["MEDIUM"] == (1, 1)


def test_clean_or_empty_report_does_not_block():
    assert scan_image.blocking({}) == []
    assert scan_image.summarize({"Results": []})["CRITICAL"] == (0, 0)
