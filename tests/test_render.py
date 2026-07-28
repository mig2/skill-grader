"""Tests for render.py — report generation."""

from scripts.render import render_markdown, render_html
from scripts.score import DIMENSION_NAMES


def _make_grade_result(overall=75.0, grade="C", blockers=False):
    """Build a minimal grade result for testing."""
    scores = {i: 3 for i in range(1, 12)}
    return {
        "overall_score": overall,
        "letter_grade": grade,
        "capped_by_blocker": blockers,
        "profile": "balanced",
        "na_dimensions": [],
        "dimension_scores": scores,
        "dimension_details": {
            i: {"name": DIMENSION_NAMES[i], "score": 3, "weight": 1.0,
                "weighted_contribution": 3.0}
            for i in range(1, 12)
        },
        "findings": [
            {
                "dimension": 3,
                "severity": "major",
                "location": "SKILL.md:42",
                "problem": "SKILL.md exceeds 500-line budget",
                "suggested_fix": "Move detailed tables to references/",
            },
            {
                "dimension": 10,
                "severity": "nit",
                "location": "SKILL.md:10",
                "problem": "Minor: broad read pattern",
                "suggested_fix": "Narrow glob pattern",
            },
        ],
        "scan": {"skill_path": "/test/skill", "skill_md_lines": 120},
        "delta": None,
        "baseline_status": "initial",
    }


class TestRenderMarkdown:
    def test_contains_grade(self):
        md = render_markdown(_make_grade_result())
        assert "C" in md
        assert "75.0" in md

    def test_contains_dimension_table(self):
        md = render_markdown(_make_grade_result())
        assert "Description Triggering" in md
        assert "Progressive Disclosure" in md

    def test_findings_grouped_by_severity(self):
        md = render_markdown(_make_grade_result())
        major_pos = md.index("major")
        nit_pos = md.index("nit")
        assert major_pos < nit_pos

    def test_blocker_noted(self):
        md = render_markdown(_make_grade_result(grade="F", blockers=True))
        assert "blocker" in md.lower() or "capped" in md.lower()

    def test_na_dimensions_shown(self):
        result = _make_grade_result()
        result["na_dimensions"] = [11]
        md = render_markdown(result)
        assert "N/A" in md

    def test_delta_shown_when_present(self):
        result = _make_grade_result()
        result["delta"] = {1: 1, 2: -1, 3: 0, 4: 0, 5: 0,
                           6: 0, 7: 0, 8: 0, 9: 0, 10: 0, 11: 0}
        result["baseline_status"] = "compared"
        md = render_markdown(result)
        assert "+1" in md or "regression" in md.lower()


class TestRenderHtml:
    def test_contains_html_structure(self):
        html = render_html(_make_grade_result())
        assert "<html" in html
        assert "</html>" in html
        assert "<style>" in html  # self-contained CSS

    def test_contains_score(self):
        html = render_html(_make_grade_result())
        assert "75.0" in html
        assert "C" in html

    def test_no_external_assets(self):
        html = render_html(_make_grade_result())
        assert 'href="http' not in html
        assert 'src="http' not in html
