"""Tests for scan.py mechanical checks."""

import json
import subprocess
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
            "deterministic_prose_signals", "mode",
        }
        assert expected_keys.issubset(result.keys())


def _make_skill(root, *, stamp=False, git=False, extra=()):
    """Build a minimal skill directory for mode/furniture tests."""
    root.mkdir(parents=True, exist_ok=True)
    (root / "SKILL.md").write_text("# Skill\n\nSee references/guide.md\n")
    (root / "references").mkdir(exist_ok=True)
    (root / "references" / "guide.md").write_text("# Guide\n")
    if stamp:
        (root / ".installed-from").write_text("abc1234\n")
    if git:
        (root / ".git").mkdir(exist_ok=True)
    for rel in extra:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# filler\n")
    return root


class TestModeDetection:
    def test_installed_from_stamp_means_installed(self, tmp_path):
        skill = _make_skill(tmp_path / "s", stamp=True)
        assert scan_skill(skill)["mode"] == "installed"

    def test_git_dir_means_codebase(self, tmp_path):
        skill = _make_skill(tmp_path / "s", git=True)
        assert scan_skill(skill)["mode"] == "codebase"

    def test_stamp_wins_over_git(self, tmp_path):
        skill = _make_skill(tmp_path / "s", stamp=True, git=True)
        assert scan_skill(skill)["mode"] == "installed"

    def test_bare_directory_defaults_to_codebase(self, tmp_path):
        skill = _make_skill(tmp_path / "s")
        assert scan_skill(skill)["mode"] == "codebase"


class TestFurnitureExclusion:
    FURNITURE = ("docs/plan.md", "README.md", "LICENSE.md", "install.sh")

    def test_codebase_mode_ignores_furniture(self, tmp_path):
        skill = _make_skill(
            tmp_path / "s", git=True,
            extra=self.FURNITURE + ("references/orphan.md",),
        )
        orphans = scan_skill(skill)["orphaned_files"]
        assert orphans == ["references/orphan.md"]

    def test_installed_mode_counts_furniture(self, tmp_path):
        skill = _make_skill(tmp_path / "s", stamp=True, extra=self.FURNITURE)
        orphans = scan_skill(skill)["orphaned_files"]
        assert "docs/plan.md" in orphans
        assert "README.md" in orphans

    def test_gitignored_output_is_not_an_orphan(self, tmp_path):
        """Generated output the repo already declares non-source is excluded."""
        skill = _make_skill(
            tmp_path / "s", extra=("grade.md", "references/orphan.md"),
        )
        (skill / ".gitignore").write_text("grade.md\n")
        subprocess.run(["git", "init", "-q"], cwd=skill, check=True)

        orphans = scan_skill(skill)["orphaned_files"]
        assert orphans == ["references/orphan.md"]

    def test_furniture_only_matched_at_root(self, tmp_path):
        """A docs/ path nested under references/ is still a real orphan."""
        skill = _make_skill(
            tmp_path / "s", git=True, extra=("references/docs/deep.md",),
        )
        assert scan_skill(skill)["orphaned_files"] == ["references/docs/deep.md"]
