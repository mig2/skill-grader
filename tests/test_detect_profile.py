"""Tests for detect_profile.py archetype heuristic."""

from pathlib import Path
from scripts.detect_profile import detect_profile

FIXTURES = Path(__file__).parent / "fixtures"


def test_gold_detects_workflow():
    """Gold fixture has scripts + tests + artifacts -> workflow."""
    result = detect_profile(FIXTURES / "gold")
    assert result["profile"] == "workflow"


def test_prose_only_detects_style_or_reference():
    """No scripts, no tests -> style or reference."""
    result = detect_profile(FIXTURES / "dim05-prose-not-script")
    assert result["profile"] in ("style", "reference", "balanced")


def test_no_scripts_with_detailed_rules_detects_style():
    """Caps-heavy skill with formatting rules -> style."""
    result = detect_profile(FIXTURES / "dim06-caps-density")
    assert result["profile"] in ("style", "balanced")


def test_result_has_required_keys():
    result = detect_profile(FIXTURES / "gold")
    assert "profile" in result
    assert "reasoning" in result
    assert "signals" in result


def test_dim11_has_scripts_no_tests():
    """Has scripts but no tests."""
    result = detect_profile(FIXTURES / "dim11-no-tests")
    assert result["profile"] in ("workflow", "balanced")
