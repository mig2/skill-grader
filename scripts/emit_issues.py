"""emit_issues.py — GitHub issue export for skill-grader findings."""

from __future__ import annotations

import csv
import hashlib
import io
import json

from scripts.score import DIMENSION_NAMES

DIMENSION_SLUGS: dict[int, str] = {
    1: "description-triggering",
    2: "trigger-surface",
    3: "progressive-disclosure",
    4: "resource-hygiene",
    5: "script-vs-prose",
    6: "instructional-voice",
    7: "output-contract",
    8: "examples",
    9: "environment-portability",
    10: "least-surprise-safety",
    11: "testability",
}

_SEVERITY_RANK = {"blocker": 2, "major": 1, "nit": 0}
_INCLUDE_SEVERITIES = {"blocker", "major"}


def _fingerprint(skill: str, dim: int, location: str, problem: str) -> str:
    raw = f"{skill}|{dim}|{location}|{problem.lower()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def findings_to_issues(findings: list[dict], skill_name: str) -> list[dict]:
    """Filter findings to blocker/major and convert to GitHub issue dicts."""
    issues = []
    for f in findings:
        severity = f.get("severity", "")
        if severity not in _INCLUDE_SEVERITIES:
            continue

        dim = f.get("dimension", 0)
        dim_name = DIMENSION_NAMES.get(dim, f"Dim {dim}")
        dim_slug = DIMENSION_SLUGS.get(dim, f"dim-{dim}")
        problem = f.get("problem", "")
        location = f.get("location", "")
        suggested_fix = f.get("suggested_fix", "")

        title = f"[skill-grader] {skill_name}: D{dim} {dim_name} — {problem[:60]}"
        labels = [f"severity:{severity}", f"dim:{dim_slug}"]
        fp = _fingerprint(skill_name, dim, location, problem)

        body = (
            f"**Problem:** {problem}\n\n"
            f"**Location:** `{location}`\n\n"
            f"**Suggested fix:** {suggested_fix}\n\n"
            f"**Rubric dimension:** D{dim} — {dim_name}\n\n"
            f"<!-- sg:{fp} -->"
        )

        issues.append({"title": title, "body": body, "labels": labels})

    return issues


def render_issues_json(issues: list[dict]) -> str:
    """Render issues as a JSON string."""
    return json.dumps(issues, indent=2)


def render_issues_csv(issues: list[dict]) -> str:
    """Render issues as CSV with columns: title, body, labels (semicolon-joined)."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["title", "body", "labels"])
    writer.writeheader()
    for issue in issues:
        writer.writerow({
            "title": issue["title"],
            "body": issue["body"],
            "labels": ";".join(issue["labels"]),
        })
    return output.getvalue()
