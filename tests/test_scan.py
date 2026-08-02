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


class TestVerificationSurfaces:
    """Unit tests and evals are separate signals and must not substitute.

    D11 asks whether the bundled scripts are tested; D12 asks whether the skill
    itself was ever evaluated. A skill can satisfy one and fail the other.
    """

    def test_gold_has_both_surfaces(self):
        result = scan_skill(FIXTURES / "gold")
        assert result["has_unit_tests"] is True
        assert result["has_trigger_evals"] is True
        assert result["has_quality_evals"] is True
        assert result["has_eval_assertions"] is True

    def test_dim11_has_evals_but_no_unit_tests(self):
        """Isolates D11: scripts ship untested, evals are present."""
        result = scan_skill(FIXTURES / "dim11-no-tests")
        assert result["has_scripts"] is True
        assert result["has_unit_tests"] is False
        assert result["has_evals"] is True

    def test_dim12_has_unit_tests_but_no_evals(self):
        """Isolates D12: scripts are tested, the skill never was."""
        result = scan_skill(FIXTURES / "dim12-no-evals")
        assert result["has_unit_tests"] is True
        assert result["has_evals"] is False
        assert result["has_trigger_evals"] is False
        assert result["has_quality_evals"] is False

    def test_unit_tests_require_recognisable_test_files(self, tmp_path):
        """A tests/ directory of fixtures verifies nothing."""
        skill = _make_skill(tmp_path / "s", extra=("tests/fixtures/sample.md",))
        assert scan_skill(skill)["has_unit_tests"] is False

    def test_empty_assertions_do_not_count(self, tmp_path):
        """skill-creator writes assertions:[] as a placeholder before drafting."""
        skill = _make_skill(tmp_path / "s")
        (skill / "evals").mkdir()
        (skill / "evals" / "evals.json").write_text(
            '{"evals": [{"id": 1, "prompt": "do a thing", "assertions": []}]}'
        )
        result = scan_skill(skill)
        assert result["has_quality_evals"] is True
        assert result["has_eval_assertions"] is False

    def test_eval_files_are_listed(self):
        result = scan_skill(FIXTURES / "gold")
        assert sorted(result["eval_files"]) == [
            "evals/evals.json",
            "evals/trigger_eval.json",
        ]


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
            "large_refs_without_toc", "has_scripts", "has_evals", "has_unit_tests",
            "has_trigger_evals", "has_quality_evals", "has_eval_assertions",
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


class TestInstallProvenance:
    def _repo(self, tmp_path):
        """A source checkout with one commit, usable as an install source."""
        src = _make_skill(tmp_path / "src")
        subprocess.run(["git", "init", "-q"], cwd=src, check=True)
        subprocess.run(["git", "add", "-A"], cwd=src, check=True)
        subprocess.run(
            ["git", "-c", "user.email=t@t", "-c", "user.name=t",
             "commit", "-qm", "init"], cwd=src, check=True,
        )
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=src,
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        return src, head

    def _install(self, tmp_path, stamp_text):
        skill = _make_skill(tmp_path / "installed")
        (skill / ".installed-from").write_text(stamp_text)
        return skill

    def test_legacy_bare_hash_still_detects_installed(self, tmp_path):
        """code-audit's original format must keep working."""
        skill = self._install(tmp_path, "b902f52\n")
        result = scan_skill(skill)
        assert result["mode"] == "installed"
        assert result["install_metadata"]["legacy"] is True
        assert result["install_metadata"]["commit"] == "b902f52"

    def test_legacy_stamp_cannot_be_checked_for_drift(self, tmp_path):
        """A bare hash names no repo, so drift is unverifiable, not zero."""
        skill = self._install(tmp_path, "b902f52\n")
        st = scan_skill(skill)["staleness"]
        assert st["checked"] is False
        assert st["commits_behind"] is None
        assert "source" in st["reason"]

    def test_current_install_reports_no_drift(self, tmp_path):
        src, head = self._repo(tmp_path)
        skill = self._install(tmp_path, json.dumps({
            "source_path": str(src), "commit": head, "dirty": False,
        }))
        st = scan_skill(skill)["staleness"]
        assert st["checked"] is True
        assert st["commits_behind"] == 0
        assert st["payload_changed"] is False

    def test_drift_outside_the_payload_is_not_staleness(self, tmp_path):
        """A docs-only commit leaves the deployed skill current."""
        src, head = self._repo(tmp_path)
        (src / "docs").mkdir()
        (src / "docs" / "notes.md").write_text("# notes\n")
        subprocess.run(["git", "add", "-A"], cwd=src, check=True)
        subprocess.run(
            ["git", "-c", "user.email=t@t", "-c", "user.name=t",
             "commit", "-qm", "docs"], cwd=src, check=True,
        )
        skill = self._install(tmp_path, json.dumps({
            "source_path": str(src), "commit": head, "dirty": False,
        }))
        st = scan_skill(skill)["staleness"]
        assert st["commits_behind"] == 1
        assert st["payload_changed"] is False

    def test_payload_drift_is_staleness(self, tmp_path):
        src, head = self._repo(tmp_path)
        (src / "SKILL.md").write_text("# Skill\n\nSee references/guide.md\n\nnew\n")
        subprocess.run(["git", "add", "-A"], cwd=src, check=True)
        subprocess.run(
            ["git", "-c", "user.email=t@t", "-c", "user.name=t",
             "commit", "-qm", "edit skill"], cwd=src, check=True,
        )
        skill = self._install(tmp_path, json.dumps({
            "source_path": str(src), "commit": head, "dirty": False,
        }))
        st = scan_skill(skill)["staleness"]
        assert st["commits_behind"] == 1
        assert st["payload_changed"] is True

    def test_missing_source_is_unverifiable_not_current(self, tmp_path):
        skill = self._install(tmp_path, json.dumps({
            "source_path": str(tmp_path / "gone"), "commit": "abc123",
            "dirty": False,
        }))
        st = scan_skill(skill)["staleness"]
        assert st["checked"] is False
        assert "not found" in st["reason"]

    def test_dirty_install_is_flagged(self, tmp_path):
        src, head = self._repo(tmp_path)
        skill = self._install(tmp_path, json.dumps({
            "source_path": str(src), "commit": head, "dirty": True,
        }))
        assert scan_skill(skill)["staleness"]["dirty_at_install"] is True


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

    def test_file_referenced_only_from_a_script_is_not_an_orphan(self, tmp_path):
        """A template loaded by code is used, even if no prose names it."""
        skill = _make_skill(tmp_path / "s", stamp=True)
        # SKILL.md names the script; only the template's discovery is under test.
        (skill / "SKILL.md").write_text(
            "# Skill\n\nSee references/guide.md\n\nRun scripts/render.py\n"
        )
        (skill / "assets").mkdir()
        (skill / "assets" / "report.template").write_text("<html></html>")
        (skill / "scripts").mkdir()
        (skill / "scripts" / "render.py").write_text(
            'TEMPLATE = "assets/report.template"\n'
        )
        assert scan_skill(skill)["orphaned_files"] == []

    def test_package_marker_is_never_an_orphan(self, tmp_path):
        skill = _make_skill(tmp_path / "s", stamp=True)
        (skill / "scripts").mkdir()
        (skill / "scripts" / "__init__.py").write_text("")
        assert scan_skill(skill)["orphaned_files"] == []

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
