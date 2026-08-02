"""Tests for render.py — report generation."""

from scripts.render import render_markdown, render_html, describe_staleness
from scripts.score import DIMENSION_NAMES


def _make_grade_result(overall=75.0, grade="C", blockers=False):
    """Build a minimal grade result for testing."""
    scores = {i: 3 for i in range(1, 13)}
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
            for i in range(1, 13)
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


class TestModeNote:
    def _with_mode(self, mode):
        result = _make_grade_result()
        result["scan"]["mode"] = mode
        return result

    def test_installed_note_points_at_codebase(self):
        md = render_markdown(self._with_mode("installed"))
        assert "installed skill" in md
        assert "source checkout" in md

    def test_codebase_note_points_at_installed(self):
        md = render_markdown(self._with_mode("codebase"))
        assert "skill codebase" in md
        assert "installed skill" in md

    def test_note_appears_in_html(self):
        html = render_html(self._with_mode("installed"))
        assert "mode-note" in html
        assert "installed skill" in html

    def test_absent_mode_renders_no_note(self):
        md = render_markdown(_make_grade_result())
        assert "installed skill" not in md
        assert "skill codebase" not in md


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


class TestStalenessNote:
    def _scan(self, **st):
        return {"scan": {"skill_path": "/s", "mode": "installed", "staleness": st}}

    def test_codebase_target_gets_no_provenance_line(self):
        scan = {"skill_path": "/s", "mode": "codebase", "staleness": {"checked": False}}
        assert describe_staleness(scan) is None

    def test_current_payload_reads_as_current(self):
        note = describe_staleness(self._scan(checked=True, commits_behind=0)["scan"])
        assert "matches the source" in note

    def test_non_payload_drift_is_not_reported_as_stale(self):
        note = describe_staleness(
            self._scan(checked=True, commits_behind=2, payload_changed=False)["scan"]
        )
        assert "current" in note
        assert "Stale" not in note

    def test_payload_drift_says_reinstall(self):
        note = describe_staleness(
            self._scan(checked=True, commits_behind=1, payload_changed=True)["scan"]
        )
        assert "Stale" in note
        assert "install.sh" in note

    def test_dirty_install_outranks_drift(self):
        note = describe_staleness(
            self._scan(checked=True, commits_behind=0, dirty_at_install=True)["scan"]
        )
        assert "uncommitted" in note


class TestZeroScoreRendering:
    def test_zero_renders_as_zero_not_question_mark(self):
        result = _make_grade_result()
        result["dimension_details"] = {}
        result["dimension_scores"][12] = 0
        md = render_markdown(result)
        row = [l for l in md.splitlines() if l.startswith("| 12 |")][0]
        assert "0 / 4" in row
        assert "?" not in row

    def test_weight_column_reflects_details(self):
        result = _make_grade_result()
        result["dimension_details"][5] = {
            "name": "Script vs. Prose Allocation", "score": 3,
            "weight": 1.5, "weighted_contribution": 4.5,
        }
        md = render_markdown(result)
        row = [l for l in md.splitlines() if l.startswith("| 5 |")][0]
        assert "1.5" in row


class TestPartialAssessmentRendering:
    def _partial(self):
        r = _make_grade_result()
        r["partial_assessment"] = True
        r["overall_score"] = None
        r["letter_grade"] = None
        r["unscoreable_dimensions"] = [11, 12]
        r["scan"]["mode"] = "installed"
        return r

    def test_no_headline_grade_in_markdown(self):
        md = render_markdown(self._partial())
        assert "Partial assessment" in md
        assert "/ 100" not in md.split("## Dimension")[0]

    def test_names_what_could_not_be_assessed(self):
        md = render_markdown(self._partial())
        assert "Not assessable on this target" in md
        assert "Script Correctness" in md and "Behavioral Evals" in md

    def test_table_distinguishes_na_from_not_assessable(self):
        r = self._partial()
        r["na_dimensions"] = [5]
        md = render_markdown(r)
        rows = {l.split("|")[1].strip(): l for l in md.splitlines() if l.startswith("| ")}
        assert "N/A" in rows["5"]
        assert "not assessable" in rows["11"]

    def test_html_does_not_crash_without_a_letter(self):
        html = render_html(self._partial())
        assert "grade-partial" in html
        assert "Partial assessment" in html
