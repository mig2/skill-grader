"""Tests for score.py — weighted scoring and baseline delta."""

from pathlib import Path
from scripts.score import (
    load_profiles,
    compute_score,
    to_letter_grade,
    compute_delta,
    build_grade_result,
)

PROFILES_PATH = Path(__file__).parent.parent / "config" / "profiles.yaml"


class TestLoadProfiles:
    def test_loads_all_profiles(self):
        profiles = load_profiles(PROFILES_PATH)
        assert set(profiles.keys()) == {"workflow", "style", "reference", "balanced"}

    def test_workflow_has_elevated_weights(self):
        profiles = load_profiles(PROFILES_PATH)
        wf = profiles["workflow"]
        assert wf["weights"].get(5, 1.0) > 1.0  # script vs prose

    def test_style_has_na_dimensions(self):
        profiles = load_profiles(PROFILES_PATH)
        assert 11 in profiles["style"]["na"]


class TestComputeScore:
    def test_perfect_score_balanced(self):
        scores = {i: 4 for i in range(1, 13)}
        result = compute_score(scores, "balanced", PROFILES_PATH)
        assert result["overall_score"] == 100.0
        assert result["letter_grade"] == "A+"

    def test_zero_score(self):
        scores = {i: 0 for i in range(1, 13)}
        result = compute_score(scores, "balanced", PROFILES_PATH)
        assert result["overall_score"] == 0.0

    def test_na_dimensions_excluded(self):
        scores = {i: 4 for i in range(1, 13)}
        scores[11] = 0  # testability — N/A for style
        result = compute_score(scores, "style", PROFILES_PATH)
        assert result["overall_score"] == 100.0
        assert 11 in result["na_dimensions"]

    def test_blocker_caps_grade(self):
        scores = {i: 4 for i in range(1, 13)}
        result = compute_score(
            scores, "balanced", PROFILES_PATH, blockers=True,
        )
        assert result["letter_grade"] == "F"
        assert result["capped_by_blocker"] is True

    def test_weighted_mean_differs_from_flat(self):
        scores = {i: 2 for i in range(1, 13)}
        scores[5] = 4  # script vs prose — elevated in workflow
        result_wf = compute_score(scores, "workflow", PROFILES_PATH)
        result_bal = compute_score(scores, "balanced", PROFILES_PATH)
        assert result_wf["overall_score"] > result_bal["overall_score"]


class TestLetterGrade:
    def test_grade_boundaries(self):
        assert to_letter_grade(97) == "A+"
        assert to_letter_grade(93) == "A"
        assert to_letter_grade(90) == "A-"
        assert to_letter_grade(87) == "B+"
        assert to_letter_grade(83) == "B"
        assert to_letter_grade(80) == "B-"
        assert to_letter_grade(77) == "C+"
        assert to_letter_grade(73) == "C"
        assert to_letter_grade(70) == "C-"
        assert to_letter_grade(67) == "D+"
        assert to_letter_grade(63) == "D"
        assert to_letter_grade(60) == "D-"
        assert to_letter_grade(59) == "F"


class TestComputeDelta:
    def test_no_baseline_returns_none(self):
        current = {i: 3 for i in range(1, 13)}
        delta = compute_delta(current, None)
        assert delta is None

    def test_delta_reports_changes(self):
        old = {i: 2 for i in range(1, 13)}
        new = {i: 3 for i in range(1, 13)}
        new[1] = 1  # regression
        delta = compute_delta(new, old)
        assert delta[1] == -1  # regression
        assert delta[2] == +1  # improvement

    def test_delta_no_change(self):
        scores = {i: 3 for i in range(1, 13)}
        delta = compute_delta(scores, scores)
        assert all(v == 0 for v in delta.values())
