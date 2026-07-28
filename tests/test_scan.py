"""Tests for scan.py mechanical checks."""

import json
from pathlib import Path
from scripts.scan import scan_skill

FIXTURES = Path(__file__).parent / "fixtures"


class TestLineCount:
    def test_gold_under_budget(self):
        result = scan_skill(FIXTURES / "gold")
        assert result["skill_md_lines"] <= 500

    def test_no_disclosure_over_budget(self):
        result = scan_skill(FIXTURES / "dim03-no-disclosure")
        assert result["skill_md_lines"] > 500


class TestOrphanedFiles:
    def test_gold_no_orphans(self):
        result = scan_skill(FIXTURES / "gold")
        assert result["orphaned_files"] == []

    def test_dim04_has_orphans(self):
        result = scan_skill(FIXTURES / "dim04-orphaned-files")
        assert len(result["orphaned_files"]) > 0
        assert any("orphan" in f for f in result["orphaned_files"])


class TestDanglingRefs:
    def test_gold_no_dangling(self):
        result = scan_skill(FIXTURES / "gold")
        assert result["dangling_refs"] == []


class TestCapsDensity:
    def test_gold_low_caps(self):
        result = scan_skill(FIXTURES / "gold")
        assert result["caps_density"] < 0.05

    def test_dim06_high_caps(self):
        result = scan_skill(FIXTURES / "dim06-caps-density")
        assert result["caps_density"] > 0.10


class TestTocPresence:
    def test_large_ref_without_toc(self):
        result = scan_skill(FIXTURES / "dim03-no-disclosure")
        assert isinstance(result["large_refs_without_toc"], list)


class TestResourceGraph:
    def test_gold_all_files_referenced(self):
        result = scan_skill(FIXTURES / "gold")
        assert result["orphaned_files"] == []
        assert result["dangling_refs"] == []

    def test_has_scripts(self):
        result = scan_skill(FIXTURES / "gold")
        assert result["has_scripts"] is True

    def test_no_scripts(self):
        result = scan_skill(FIXTURES / "dim05-prose-not-script")
        assert result["has_scripts"] is False


class TestHasEvals:
    def test_gold_has_evals(self):
        result = scan_skill(FIXTURES / "gold")
        assert result["has_evals"] is True

    def test_dim11_no_evals(self):
        result = scan_skill(FIXTURES / "dim11-no-tests")
        assert result["has_evals"] is False


class TestContentDuplication:
    def test_gold_no_duplication(self):
        result = scan_skill(FIXTURES / "gold")
        assert result["duplicated_blocks"] == []


class TestScanOutput:
    def test_result_is_serialisable(self):
        result = scan_skill(FIXTURES / "gold")
        json.dumps(result)  # should not raise

    def test_result_has_all_keys(self):
        result = scan_skill(FIXTURES / "gold")
        expected_keys = {
            "skill_path", "skill_md_lines", "orphaned_files",
            "dangling_refs", "caps_density", "caps_lines",
            "large_refs_without_toc", "has_scripts", "has_evals",
            "duplicated_blocks", "bundled_files", "referenced_files",
            "deterministic_prose_signals",
        }
        assert expected_keys.issubset(result.keys())
