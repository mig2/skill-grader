"""Tests for emit_issues.py — GitHub issue export."""

import csv
import io
import json

from scripts.emit_issues import findings_to_issues, render_issues_json, render_issues_csv


def _make_findings():
    return [
        {
            "dimension": 3,
            "severity": "major",
            "location": "SKILL.md:42",
            "problem": "SKILL.md exceeds 500-line budget",
            "suggested_fix": "Move detailed tables to references/",
        },
        {
            "dimension": 10,
            "severity": "blocker",
            "location": "SKILL.md:10",
            "problem": "Undeclared network egress",
            "suggested_fix": "Remove fetch call or declare it",
        },
        {
            "dimension": 6,
            "severity": "nit",
            "location": "SKILL.md:55",
            "problem": "Minor caps density",
            "suggested_fix": "Reduce ALL-CAPS usage",
        },
    ]


class TestFindingsToIssues:
    def test_filters_below_major(self):
        issues = findings_to_issues(_make_findings(), "my-skill")
        assert len(issues) == 2

    def test_title_format(self):
        issues = findings_to_issues(_make_findings(), "my-skill")
        assert issues[0]["title"].startswith("[skill-grader] my-skill:")

    def test_labels_include_severity_and_dimension(self):
        issues = findings_to_issues(_make_findings(), "my-skill")
        labels = issues[0]["labels"]
        assert "severity:major" in labels or "severity:blocker" in labels

    def test_body_contains_fingerprint(self):
        issues = findings_to_issues(_make_findings(), "my-skill")
        assert "<!-- sg:" in issues[0]["body"]

    def test_fingerprint_is_stable(self):
        issues1 = findings_to_issues(_make_findings(), "my-skill")
        issues2 = findings_to_issues(_make_findings(), "my-skill")
        assert issues1[0]["body"] == issues2[0]["body"]


class TestRenderFormats:
    def test_json_is_valid(self):
        issues = findings_to_issues(_make_findings(), "my-skill")
        output = render_issues_json(issues)
        parsed = json.loads(output)
        assert isinstance(parsed, list)

    def test_csv_is_valid(self):
        issues = findings_to_issues(_make_findings(), "my-skill")
        output = render_issues_csv(issues)
        reader = csv.DictReader(io.StringIO(output))
        rows = list(reader)
        assert len(rows) == 2
        assert "title" in rows[0]
