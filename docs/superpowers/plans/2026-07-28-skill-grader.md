# skill-grader Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Claude Skill that grades other skills against an 11-dimension rubric, producing actionable reports in Markdown, HTML, and JSON.

**Architecture:** Scripts handle mechanical checks and scoring math; the model handles judgment-based dimensions. `scan.py` extracts measurements, `detect_profile.py` picks a weight profile, `score.py` computes grades, `render.py` and `emit_issues.py` produce outputs. SKILL.md orchestrates the workflow.

**Tech Stack:** Python 3.13, uv, PyYAML, Jinja2, pytest

---

### Task 1: Project scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `config/profiles.yaml`
- Create: `scripts/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `.python-version`
- Create: `.gitignore`

- [ ] **Step 1: Initialize uv project**

```bash
cd /Users/mattgreenwood/Code/skill-skill-grader
uv init --no-readme
```

- [ ] **Step 2: Set Python version and add dependencies**

```bash
uv python pin 3.13
uv add pyyaml jinja2
uv add --dev pytest
```

- [ ] **Step 3: Create directory structure**

```bash
mkdir -p scripts tests/fixtures config assets references
touch scripts/__init__.py tests/__init__.py
```

- [ ] **Step 4: Write config/profiles.yaml**

```yaml
# Weight profiles for skill archetypes.
# Each dimension weight defaults to 1.0 if omitted.
# Dimensions listed under `na` are excluded and renormalised.

profiles:
  workflow:
    description: "Multi-step pipelines with scripts and artifacts"
    weights:
      4: 1.5    # resource hygiene
      5: 1.5    # script vs prose
      7: 1.5    # output contract
      11: 1.5   # testability

  style:
    description: "House-style and formatting rules"
    weights:
      6: 1.5    # instructional voice
      7: 1.5    # output contract
      8: 1.5    # examples
    na: [11]    # output is judged, not asserted

  reference:
    description: "Domain knowledge, minimal procedure"
    weights:
      2: 1.5    # trigger surface coverage
      3: 1.5    # progressive disclosure
      4: 1.5    # resource hygiene
    na: [5, 11] # no scripts expected, no objective assertions

  balanced:
    description: "Fallback when archetype is unclear"
    # all weights 1.0, no N/A
```

- [ ] **Step 5: Write tests/conftest.py with shared fixtures**

```python
"""Shared pytest fixtures for skill-grader tests."""

from pathlib import Path
import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir():
    return FIXTURES_DIR


@pytest.fixture
def gold_skill(fixtures_dir):
    return fixtures_dir / "gold"


@pytest.fixture
def profiles_path():
    return Path(__file__).parent.parent / "config" / "profiles.yaml"
```

- [ ] **Step 6: Write .gitignore**

```
__pycache__/
*.pyc
.venv/
*.egg-info/
dist/
.skill-grader/
```

- [ ] **Step 7: Init git and commit**

```bash
git init
git add .
git commit -m "chore: scaffold project with uv, profiles, test setup"
```

---

### Task 2: Rubric reference and test fixtures (co-designed)

**Files:**
- Create: `references/rubric.md`
- Create: `tests/fixtures/gold/SKILL.md`
- Create: `tests/fixtures/gold/references/guide.md`
- Create: `tests/fixtures/gold/scripts/process.py`
- Create: `tests/fixtures/gold/tests/test_eval.py`
- Create: `tests/fixtures/dim01-bad-trigger/SKILL.md`
- Create: `tests/fixtures/dim02-narrow-surface/SKILL.md`
- Create: `tests/fixtures/dim03-no-disclosure/SKILL.md`
- Create: `tests/fixtures/dim04-orphaned-files/SKILL.md`
- Create: `tests/fixtures/dim04-orphaned-files/references/guide.md`
- Create: `tests/fixtures/dim04-orphaned-files/references/orphan.md`
- Create: `tests/fixtures/dim05-prose-not-script/SKILL.md`
- Create: `tests/fixtures/dim06-caps-density/SKILL.md`
- Create: `tests/fixtures/dim07-loose-contract/SKILL.md`
- Create: `tests/fixtures/dim08-bad-examples/SKILL.md`
- Create: `tests/fixtures/dim09-not-portable/SKILL.md`
- Create: `tests/fixtures/dim10-unsafe/SKILL.md`
- Create: `tests/fixtures/dim11-no-tests/SKILL.md`
- Create: `tests/fixtures/dim11-no-tests/scripts/run.py`

These are co-designed: write rubric descriptors, then write a fixture that concretely fails each one. The fixture validates the descriptor is specific enough to discriminate.

- [ ] **Step 1: Write references/rubric.md**

This is a large reference file. Write the full anchored 0-4 descriptors for all 11 dimensions. Each dimension gets a table with score 0 through 4, where each cell describes the concrete observable that earns that score. Structure:

```markdown
# Rubric — Anchored Descriptors

Each dimension is scored 0-4. Scores are assigned by matching the skill against the anchored descriptors below. Pick the highest descriptor that fully applies.

---

## Dimension 1: Description Triggering

| Score | Descriptor |
|-------|-----------|
| 0 | Description is missing or states only capability ("helps with X") with no trigger context. |
| 1 | Description mentions a context but is vague ("use for code tasks"). No concrete trigger phrases. |
| 2 | Description states what and when, but trigger phrases are generic. Missing negative scope where boundaries are contestable. |
| 3 | Clear what/when with concrete trigger phrases. Negative scope present where needed. Slightly under-assertive — could miss oblique invocations. |
| 4 | Precise what/when, concrete trigger phrases covering direct and oblique invocations, negative scope where boundaries are contestable, appropriately assertive. |

## Dimension 2: Trigger Surface Coverage

| Score | Descriptor |
|-------|-----------|
| 0 | No trigger phrases or contexts stated. |
| 1 | One or two literal trigger phrases. Would miss most realistic user phrasings. |
| 2 | Covers direct phrasings but misses oblique or indirect requests. No mention of sibling skill collisions. |
| 3 | Covers direct and some oblique phrasings. Sibling collisions acknowledged where relevant. |
| 4 | Comprehensive coverage of direct, oblique, and edge-case phrasings. Sibling skill boundaries explicitly drawn. |

## Dimension 3: Progressive Disclosure

| Score | Descriptor |
|-------|-----------|
| 0 | SKILL.md exceeds 800 lines with no use of references/. |
| 1 | SKILL.md exceeds 500 lines. Some content could be pushed to references/ but isn't. |
| 2 | SKILL.md is within budget (~500 lines) but reference files over 300 lines lack a table of contents. |
| 3 | SKILL.md within budget, references used appropriately, large reference files have TOCs. Minor disclosure issues. |
| 4 | SKILL.md is concise and focused. Detail correctly pushed to references/. All reference files over 300 lines have a TOC. Clear navigation. |

## Dimension 4: Resource Hygiene

| Score | Descriptor |
|-------|-----------|
| 0 | Multiple orphaned files and/or dangling references. Significant content duplication between SKILL.md and references. |
| 1 | Orphaned files or dangling references present. Some duplication. |
| 2 | No orphans or dangling refs, but non-trivial content duplicated between SKILL.md and a reference file. |
| 3 | Clean references — no orphans, no dangling refs, minimal duplication. Minor issues only. |
| 4 | Every bundled file is referenced and exists. Zero content duplication. Clean resource graph. |

## Dimension 5: Script vs. Prose Allocation

| Score | Descriptor |
|-------|-----------|
| 0 | Deterministic, repetitive work (line counting, file scanning, formatting) described entirely as prose steps for the model to execute manually. |
| 1 | Most deterministic work is prose. One or two scripts exist but cover only a fraction of what should be automated. |
| 2 | Mix of scripts and prose. Some deterministic work still described as manual steps. |
| 3 | Most deterministic work is scripted. Prose reserved for judgment-requiring steps. Minor gaps. |
| 4 | All deterministic/repetitive work is scripted. Prose is used only where model judgment is genuinely required. Scripts are well-structured and support --help. |

## Dimension 6: Instructional Voice

| Score | Descriptor |
|-------|-----------|
| 0 | Passive or ambiguous voice. Instructions read as descriptions rather than directives. |
| 1 | Mix of imperative and passive. Heavy use of ALL-CAPS imperatives (>5% of instruction lines) as a substitute for rationale. |
| 2 | Mostly imperative. Some ALL-CAPS density. Rationale provided for some mandates but not others. |
| 3 | Consistent imperative voice. Rationale-over-mandate — most rules explain why. Low ALL-CAPS density. |
| 4 | Clean imperative voice throughout. Every non-obvious mandate has a rationale. ALL-CAPS used sparingly and only for genuine safety/correctness constraints. |

## Dimension 7: Output Contract

| Score | Descriptor |
|-------|-----------|
| 0 | Skill produces artifacts but format is not specified. |
| 1 | Format is mentioned ("outputs a report") but not pinned to a template or schema. |
| 2 | Format partially specified — some fields defined, others left to model discretion. |
| 3 | Format pinned to a template or schema. Minor ambiguities in edge cases. |
| 4 | Exact output template or schema defined. All fields, ordering, and formatting specified. Run-to-run consistency is achievable from the contract alone. |

## Dimension 8: Examples

| Score | Descriptor |
|-------|-----------|
| 0 | No examples provided. |
| 1 | Examples present but overfit to a single narrow case. Would anchor the model to one pattern. |
| 2 | Examples cover one case well but don't generalise. Missing variation in inputs or contexts. |
| 3 | Multiple examples that cover different cases. Minor gaps in coverage. |
| 4 | Examples that generalise — cover different input types, edge cases, and contexts. Clearly illustrate the principle rather than a single application. |

## Dimension 9: Environment Portability

| Score | Descriptor |
|-------|-----------|
| 0 | Assumes specific environment (subagents, CLI tools, browser) with no acknowledgment. Would silently fail in other contexts. |
| 1 | Environment assumptions present but partially documented. No graceful degradation. |
| 2 | Assumptions documented but degradation is vague ("may not work in all environments"). |
| 3 | Assumptions documented with specific degradation paths. Minor gaps. |
| 4 | All environment assumptions declared. Graceful degradation with explicit fallback behaviour stated for each dependency. |

## Dimension 10: Least Surprise / Safety

| Score | Descriptor |
|-------|-----------|
| 0 | Contents do not match stated intent. Unexpected network egress, filesystem writes outside declared paths, or instruction-injection surface present. **Any finding here is an automatic blocker.** |
| 1 | Intent mostly matches but undeclared side effects present (e.g., writes to undeclared paths). |
| 2 | No undeclared side effects but instruction-injection surface exists in bundled files (e.g., user-controlled content interpolated into prompts). |
| 3 | Clean safety posture with minor concerns (e.g., broad filesystem read patterns). |
| 4 | Contents exactly match stated intent. No unexpected side effects. No injection surface. Declared paths only. |

## Dimension 11: Testability

| Score | Descriptor |
|-------|-----------|
| 0 | No evals, no test fixtures, no way to verify the skill works. |
| 1 | Informal testing notes but no structured evals. |
| 2 | Some eval structure exists but assertions are missing or test only happy paths. |
| 3 | Structured evals with assertions for objective outputs. Subjective outputs correctly lack hard assertions. Minor coverage gaps. |
| 4 | Comprehensive eval suite. Objective outputs have objective assertions. Subjective outputs tested for structure/format without over-constraining content. Fixtures cover edge cases. |
```

- [ ] **Step 2: Write gold fixture**

Create `tests/fixtures/gold/SKILL.md` — a well-formed skill (~80 lines) that should score 3-4 on all dimensions. Include proper frontmatter, clear trigger description with negative scope, imperative voice with rationale, output contract with template, generalising examples, environment portability with degradation, and references to bundled files.

Create `tests/fixtures/gold/references/guide.md` (~50 lines, referenced from SKILL.md).
Create `tests/fixtures/gold/scripts/process.py` (minimal script, referenced from SKILL.md).
Create `tests/fixtures/gold/tests/test_eval.py` (minimal eval, referenced from SKILL.md).

- [ ] **Step 3: Write dim01-bad-trigger fixture**

`tests/fixtures/dim01-bad-trigger/SKILL.md` — description says only "Helps with code" with no trigger context, no when, no negative scope. Otherwise reasonable skill content. Expected: dimension 1 scores 0-1.

- [ ] **Step 4: Write dim02-narrow-surface fixture**

`tests/fixtures/dim02-narrow-surface/SKILL.md` — description triggers only on exact phrase "run the linter" and nothing else. Misses oblique phrasings like "check code quality" or "lint this". Expected: dimension 2 scores 0-1.

- [ ] **Step 5: Write dim03-no-disclosure fixture**

`tests/fixtures/dim03-no-disclosure/SKILL.md` — 600+ lines, everything crammed into SKILL.md, no references/ directory. Expected: dimension 3 scores 0-1.

Generate the long content by including verbose rubric tables, detailed examples, and inline reference material that should be in separate files.

- [ ] **Step 6: Write dim04-orphaned-files fixture**

`tests/fixtures/dim04-orphaned-files/SKILL.md` — references `references/guide.md` but NOT `references/orphan.md`. Create both files. `orphan.md` is present but never referenced from SKILL.md. Expected: dimension 4 scores 1-2.

- [ ] **Step 7: Write dim05-prose-not-script fixture**

`tests/fixtures/dim05-prose-not-script/SKILL.md` — describes line counting, file scanning, and format checking as prose steps: "Count the lines in the file. If more than 500, flag it." No scripts/ directory. Expected: dimension 5 scores 0-1.

- [ ] **Step 8: Write dim06-caps-density fixture**

`tests/fixtures/dim06-caps-density/SKILL.md` — heavy ALL-CAPS usage: "You MUST ALWAYS check EVERY file. NEVER skip this step. It is CRITICAL that you ALWAYS do this. IMPORTANT: ALWAYS verify." Expected: dimension 6 scores 0-1.

- [ ] **Step 9: Write dim07-loose-contract fixture**

`tests/fixtures/dim07-loose-contract/SKILL.md` — says "produce a report with your findings" but no template, schema, or format specification. Expected: dimension 7 scores 0-1.

- [ ] **Step 10: Write dim08-bad-examples fixture**

`tests/fixtures/dim08-bad-examples/SKILL.md` — one example that is extremely narrow and specific to a single file type. Would anchor the model. Expected: dimension 8 scores 1.

- [ ] **Step 11: Write dim09-not-portable fixture**

`tests/fixtures/dim09-not-portable/SKILL.md` — assumes subagents, `claude` CLI, and browser access with no acknowledgment or degradation paths. Expected: dimension 9 scores 0-1.

- [ ] **Step 12: Write dim10-unsafe fixture**

`tests/fixtures/dim10-unsafe/SKILL.md` — skill description says "analyzes code" but instructions include writing to `/tmp/exfil.log` and fetching a remote URL. Intent mismatch. Expected: dimension 10 scores 0 (blocker).

- [ ] **Step 13: Write dim11-no-tests fixture**

`tests/fixtures/dim11-no-tests/SKILL.md` — has `scripts/run.py` but no tests/ directory, no evals, no fixtures. Create the script file. Expected: dimension 11 scores 0.

- [ ] **Step 14: Commit**

```bash
git add references/rubric.md tests/fixtures/
git commit -m "feat: add rubric descriptors and test fixtures for all 11 dimensions"
```

---

### Task 3: scan.py — mechanical checks

**Files:**
- Create: `scripts/scan.py`
- Create: `tests/test_scan.py`

`scan.py` extracts mechanical measurements from a skill directory. No model judgment — just counts and file graph analysis. Outputs a `scan_result` dict.

- [ ] **Step 1: Write failing tests for scan.py**

```python
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
        # No refs at all, so no large-ref-without-toc findings
        # This dimension is about SKILL.md length primarily
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_scan.py -v
```

Expected: ImportError — `scripts.scan` does not exist yet.

- [ ] **Step 3: Implement scan.py**

```python
"""Mechanical checks for skill grading. No model judgment."""

from __future__ import annotations

import re
from pathlib import Path

# Patterns that signal deterministic work described as prose
DETERMINISTIC_PROSE_PATTERNS = [
    re.compile(r"count\s+(the\s+)?(lines|words|characters)", re.I),
    re.compile(r"check\s+(if|whether|that)\s+(the\s+)?file", re.I),
    re.compile(r"list\s+(all|every|each)\s+(file|director)", re.I),
    re.compile(r"scan\s+(the\s+)?(director|folder|file)", re.I),
    re.compile(r"measure\s+(the\s+)?(length|size|count)", re.I),
    re.compile(r"calculate\s+(the\s+)?(number|total|sum)", re.I),
]

ALL_CAPS_WORD = re.compile(r"\b[A-Z]{2,}\b")
IMPERATIVE_WORDS = {"MUST", "NEVER", "ALWAYS", "CRITICAL", "IMPORTANT",
                    "REQUIRED", "SHALL", "ABSOLUTELY", "MANDATORY"}

TOC_MARKERS = {"## table of contents", "## toc", "## contents",
               "<!-- toc -->", "[toc]"}

# File extensions to consider as "bundled content"
CONTENT_EXTENSIONS = {".md", ".txt", ".yaml", ".yml", ".json",
                      ".py", ".sh", ".bash", ".html", ".css",
                      ".js", ".ts", ".template"}


def scan_skill(skill_path: Path) -> dict:
    """Run all mechanical checks on a skill directory.

    Args:
        skill_path: Path to the skill root (must contain SKILL.md).

    Returns:
        Dict of mechanical measurements.
    """
    skill_path = Path(skill_path)
    skill_md = skill_path / "SKILL.md"

    if not skill_md.exists():
        raise FileNotFoundError(f"No SKILL.md found in {skill_path}")

    skill_text = skill_md.read_text(encoding="utf-8")
    skill_lines = skill_text.splitlines()

    bundled = _find_bundled_files(skill_path)
    referenced = _find_referenced_files(skill_path, skill_text, bundled)

    orphaned = sorted(set(bundled) - set(referenced) - {"SKILL.md"})
    dangling = sorted(set(referenced) - set(bundled) - {"SKILL.md"})

    caps_density, caps_lines = _measure_caps_density(skill_lines)
    large_no_toc = _find_large_refs_without_toc(skill_path)
    duplication = _find_duplicated_blocks(skill_path, skill_text, bundled)
    det_prose = _find_deterministic_prose(skill_lines)

    return {
        "skill_path": str(skill_path),
        "skill_md_lines": len(skill_lines),
        "orphaned_files": orphaned,
        "dangling_refs": dangling,
        "caps_density": caps_density,
        "caps_lines": caps_lines,
        "large_refs_without_toc": large_no_toc,
        "has_scripts": (skill_path / "scripts").is_dir()
            and any((skill_path / "scripts").iterdir()),
        "has_evals": _has_evals(skill_path),
        "duplicated_blocks": duplication,
        "bundled_files": sorted(bundled),
        "referenced_files": sorted(referenced),
        "deterministic_prose_signals": det_prose,
    }


def _find_bundled_files(skill_path: Path) -> set[str]:
    """All content files in the skill directory, relative paths."""
    files = set()
    for f in skill_path.rglob("*"):
        if f.is_file() and f.suffix in CONTENT_EXTENSIONS:
            rel = str(f.relative_to(skill_path))
            if not rel.startswith("."):
                files.add(rel)
    return files


def _find_referenced_files(
    skill_path: Path, skill_text: str, bundled: set[str]
) -> set[str]:
    """Files referenced from SKILL.md or other bundled files."""
    referenced = set()
    all_texts = {"SKILL.md": skill_text}

    for rel in bundled:
        if rel == "SKILL.md":
            continue
        fp = skill_path / rel
        if fp.suffix in {".md", ".txt", ".yaml", ".yml"}:
            try:
                all_texts[rel] = fp.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                pass

    for source, text in all_texts.items():
        for candidate in bundled:
            if candidate == source:
                continue
            # Check for references: path mentions, markdown links, backtick refs
            name = Path(candidate).name
            stem = Path(candidate).stem
            if candidate in text or name in text:
                referenced.add(candidate)
            # Check relative path variants
            for variant in [candidate, candidate.replace("\\", "/")]:
                if variant in text:
                    referenced.add(candidate)

    return referenced


def _measure_caps_density(lines: list[str]) -> tuple[float, list[int]]:
    """Fraction of instruction lines containing ALL-CAPS imperative words."""
    if not lines:
        return 0.0, []

    instruction_lines = []
    in_code_block = False
    in_frontmatter = False
    frontmatter_seen = False

    for i, line in enumerate(lines):
        stripped = line.strip()
        if i == 0 and stripped == "---":
            in_frontmatter = True
            continue
        if in_frontmatter:
            if stripped == "---":
                in_frontmatter = False
                frontmatter_seen = True
            continue
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if stripped and not stripped.startswith("#") and not stripped.startswith("|"):
            instruction_lines.append((i + 1, stripped))

    if not instruction_lines:
        return 0.0, []

    caps_line_numbers = []
    for line_num, text in instruction_lines:
        words = ALL_CAPS_WORD.findall(text)
        imperative_caps = [w for w in words if w in IMPERATIVE_WORDS]
        if imperative_caps:
            caps_line_numbers.append(line_num)

    density = len(caps_line_numbers) / len(instruction_lines)
    return round(density, 4), caps_line_numbers


def _find_large_refs_without_toc(skill_path: Path) -> list[str]:
    """Reference .md files over 300 lines that lack a table of contents."""
    refs_dir = skill_path / "references"
    if not refs_dir.is_dir():
        return []

    results = []
    for f in refs_dir.rglob("*.md"):
        try:
            text = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        lines = text.splitlines()
        if len(lines) > 300:
            lower = text.lower()
            if not any(marker in lower for marker in TOC_MARKERS):
                results.append(str(f.relative_to(skill_path)))

    return sorted(results)


def _has_evals(skill_path: Path) -> bool:
    """Check for presence of test/eval files."""
    for d in ["tests", "test", "evals", "eval"]:
        test_dir = skill_path / d
        if test_dir.is_dir() and any(test_dir.rglob("*")):
            return True
    return False


def _find_duplicated_blocks(
    skill_path: Path, skill_text: str, bundled: set[str]
) -> list[dict]:
    """Find non-trivial text blocks duplicated between SKILL.md and refs."""
    duplicated = []
    skill_paragraphs = _extract_paragraphs(skill_text)

    for rel in sorted(bundled):
        if rel == "SKILL.md" or not rel.endswith(".md"):
            continue
        try:
            ref_text = (skill_path / rel).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        ref_paragraphs = _extract_paragraphs(ref_text)
        for sp in skill_paragraphs:
            if len(sp) < 80:  # skip short paragraphs
                continue
            for rp in ref_paragraphs:
                if sp == rp:
                    duplicated.append({
                        "text_preview": sp[:120],
                        "locations": ["SKILL.md", rel],
                    })

    return duplicated


def _extract_paragraphs(text: str) -> list[str]:
    """Split text into normalised paragraph blocks."""
    paragraphs = []
    current = []
    in_code_block = False

    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if line.strip():
            current.append(line.strip())
        elif current:
            paragraphs.append(" ".join(current))
            current = []

    if current:
        paragraphs.append(" ".join(current))

    return paragraphs


def _find_deterministic_prose(lines: list[str]) -> list[dict]:
    """Find lines that describe deterministic work as prose instructions."""
    signals = []
    in_code_block = False

    for i, line in enumerate(lines):
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        for pattern in DETERMINISTIC_PROSE_PATTERNS:
            if pattern.search(line):
                signals.append({
                    "line": i + 1,
                    "text": line.strip(),
                    "pattern": pattern.pattern,
                })
                break  # one match per line

    return signals
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_scan.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/scan.py tests/test_scan.py
git commit -m "feat: add scan.py mechanical checks with tests"
```

---

### Task 4: detect_profile.py — archetype heuristic

**Files:**
- Create: `scripts/detect_profile.py`
- Create: `tests/test_detect_profile.py`

Analyses a skill's structure to guess which weight profile applies. Returns the profile name and reasoning.

- [ ] **Step 1: Write failing tests**

```python
"""Tests for detect_profile.py archetype heuristic."""

from pathlib import Path
from scripts.detect_profile import detect_profile

FIXTURES = Path(__file__).parent / "fixtures"


def test_gold_detects_workflow():
    """Gold fixture has scripts + tests + artifacts → workflow."""
    result = detect_profile(FIXTURES / "gold")
    assert result["profile"] == "workflow"


def test_prose_only_detects_style_or_reference():
    """No scripts, no tests → style or reference."""
    result = detect_profile(FIXTURES / "dim05-prose-not-script")
    assert result["profile"] in ("style", "reference", "balanced")


def test_no_scripts_with_detailed_rules_detects_style():
    """Caps-heavy skill with formatting rules → style."""
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_detect_profile.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement detect_profile.py**

```python
"""Archetype heuristic for skill weight profile selection."""

from __future__ import annotations

import re
from pathlib import Path


def detect_profile(skill_path: Path) -> dict:
    """Guess the best weight profile for a skill.

    Analyses structural signals:
    - Presence of scripts/ directory
    - Presence of tests/evals
    - Ratio of procedural to declarative content
    - Whether outputs are artifacts or transformed text

    Returns:
        Dict with 'profile', 'reasoning', and 'signals'.
    """
    skill_path = Path(skill_path)
    skill_md = skill_path / "SKILL.md"

    if not skill_md.exists():
        raise FileNotFoundError(f"No SKILL.md found in {skill_path}")

    text = skill_md.read_text(encoding="utf-8")
    signals = _gather_signals(skill_path, text)
    profile, reasoning = _classify(signals)

    return {
        "profile": profile,
        "reasoning": reasoning,
        "signals": signals,
    }


def _gather_signals(skill_path: Path, text: str) -> dict:
    """Extract structural signals from the skill."""
    has_scripts = (
        (skill_path / "scripts").is_dir()
        and any((skill_path / "scripts").iterdir())
    )
    has_tests = any(
        (skill_path / d).is_dir() and any((skill_path / d).rglob("*"))
        for d in ("tests", "test", "evals", "eval")
    )
    has_refs = (
        (skill_path / "references").is_dir()
        and any((skill_path / "references").iterdir())
    )

    # Count procedural vs declarative lines
    procedural_patterns = [
        re.compile(r"^\s*\d+\.\s", re.M),           # numbered steps
        re.compile(r"^\s*-\s*\[[ x]\]", re.M),       # checklists
        re.compile(r"\b(run|execute|call|invoke)\b", re.I),
    ]
    declarative_patterns = [
        re.compile(r"\b(style|format|voice|tone)\b", re.I),
        re.compile(r"\b(convention|rule|guideline|principle)\b", re.I),
        re.compile(r"\b(always|never|prefer|avoid)\b", re.I),
    ]

    proc_count = sum(len(p.findall(text)) for p in procedural_patterns)
    decl_count = sum(len(p.findall(text)) for p in declarative_patterns)

    # Artifact signals
    artifact_patterns = [
        re.compile(r"\b(output|emit|produce|generate|render)\b", re.I),
        re.compile(r"\.(json|html|md|csv|yaml)\b", re.I),
    ]
    artifact_count = sum(len(p.findall(text)) for p in artifact_patterns)

    # Reference/knowledge signals
    reference_patterns = [
        re.compile(r"\b(reference|lookup|consult|see also)\b", re.I),
        re.compile(r"\b(knowledge|domain|context|background)\b", re.I),
    ]
    ref_count = sum(len(p.findall(text)) for p in reference_patterns)

    return {
        "has_scripts": has_scripts,
        "has_tests": has_tests,
        "has_references": has_refs,
        "procedural_signals": proc_count,
        "declarative_signals": decl_count,
        "artifact_signals": artifact_count,
        "reference_signals": ref_count,
        "line_count": len(text.splitlines()),
    }


def _classify(signals: dict) -> tuple[str, str]:
    """Map signals to a profile name with reasoning."""
    has_scripts = signals["has_scripts"]
    has_tests = signals["has_tests"]
    proc = signals["procedural_signals"]
    decl = signals["declarative_signals"]
    artifacts = signals["artifact_signals"]
    refs = signals["reference_signals"]

    # Workflow: has scripts or tests, procedural content, artifact outputs
    if has_scripts and (has_tests or artifacts > 5):
        return "workflow", (
            "Skill has scripts/ and "
            + ("tests/" if has_tests else "artifact-producing patterns")
            + " — consistent with a multi-step pipeline."
        )

    if has_scripts and proc > decl:
        return "workflow", (
            "Skill has scripts/ and more procedural than declarative content."
        )

    # Reference: high reference signals, has references dir, low procedural
    if refs > 5 and signals["has_references"] and proc < decl:
        return "reference", (
            "Skill has references/ with domain-knowledge signals "
            "and more declarative than procedural content."
        )

    # Style: declarative-heavy, no scripts, formatting/convention language
    if not has_scripts and decl > proc and decl > 3:
        return "style", (
            "No scripts, declarative content dominates — "
            "consistent with a house-style or formatting skill."
        )

    # Balanced fallback
    return "balanced", (
        "No strong archetype signal detected. "
        f"Procedural={proc}, declarative={decl}, "
        f"scripts={has_scripts}, tests={has_tests}."
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_detect_profile.py -v
```

- [ ] **Step 5: Commit**

```bash
git add scripts/detect_profile.py tests/test_detect_profile.py
git commit -m "feat: add detect_profile.py archetype heuristic with tests"
```

---

### Task 5: score.py — weights, scoring, baseline delta

**Files:**
- Create: `scripts/score.py`
- Create: `tests/test_score.py`

Takes dimension scores (0-4) + profile name, applies weights from profiles.yaml, computes overall score (0-100), letter grade, and baseline delta.

- [ ] **Step 1: Write failing tests**

```python
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
        scores = {i: 4 for i in range(1, 12)}
        result = compute_score(scores, "balanced", PROFILES_PATH)
        assert result["overall_score"] == 100.0
        assert result["letter_grade"] == "A+"

    def test_zero_score(self):
        scores = {i: 0 for i in range(1, 12)}
        result = compute_score(scores, "balanced", PROFILES_PATH)
        assert result["overall_score"] == 0.0

    def test_na_dimensions_excluded(self):
        scores = {i: 4 for i in range(1, 12)}
        scores[11] = 0  # testability — N/A for style
        result = compute_score(scores, "style", PROFILES_PATH)
        # dim 11 is N/A for style, so score 0 there should not affect result
        assert result["overall_score"] == 100.0
        assert 11 in result["na_dimensions"]

    def test_blocker_caps_grade(self):
        scores = {i: 4 for i in range(1, 12)}
        result = compute_score(
            scores, "balanced", PROFILES_PATH, blockers=True,
        )
        assert result["letter_grade"] == "F"
        assert result["capped_by_blocker"] is True

    def test_weighted_mean_differs_from_flat(self):
        scores = {i: 2 for i in range(1, 12)}
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
        current = {i: 3 for i in range(1, 12)}
        delta = compute_delta(current, None)
        assert delta is None

    def test_delta_reports_changes(self):
        old = {i: 2 for i in range(1, 12)}
        new = {i: 3 for i in range(1, 12)}
        new[1] = 1  # regression
        delta = compute_delta(new, old)
        assert delta[1] == -1  # regression
        assert delta[2] == +1  # improvement

    def test_delta_no_change(self):
        scores = {i: 3 for i in range(1, 12)}
        delta = compute_delta(scores, scores)
        assert all(v == 0 for v in delta.values())
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_score.py -v
```

- [ ] **Step 3: Implement score.py**

```python
"""Weighted scoring, letter grades, and baseline delta computation."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

DIMENSION_NAMES = {
    1: "Description Triggering",
    2: "Trigger Surface Coverage",
    3: "Progressive Disclosure",
    4: "Resource Hygiene",
    5: "Script vs. Prose Allocation",
    6: "Instructional Voice",
    7: "Output Contract",
    8: "Examples",
    9: "Environment Portability",
    10: "Least Surprise / Safety",
    11: "Testability",
}

GRADE_BOUNDARIES = [
    (97, "A+"), (93, "A"), (90, "A-"),
    (87, "B+"), (83, "B"), (80, "B-"),
    (77, "C+"), (73, "C"), (70, "C-"),
    (67, "D+"), (63, "D"), (60, "D-"),
    (0, "F"),
]


def load_profiles(profiles_path: Path) -> dict:
    """Load weight profiles from YAML config."""
    with open(profiles_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    profiles = {}
    for name, cfg in data["profiles"].items():
        profiles[name] = {
            "description": cfg.get("description", ""),
            "weights": {int(k): v for k, v in cfg.get("weights", {}).items()},
            "na": [int(d) for d in cfg.get("na", [])],
        }
    return profiles


def compute_score(
    dimension_scores: dict[int, int],
    profile_name: str,
    profiles_path: Path,
    *,
    blockers: bool = False,
) -> dict:
    """Compute weighted overall score and letter grade.

    Args:
        dimension_scores: Dict mapping dimension number (1-11) to score (0-4).
        profile_name: Name of the weight profile to use.
        profiles_path: Path to profiles.yaml.
        blockers: If True, cap grade at F regardless of score (dim 10 blocker).

    Returns:
        Dict with overall_score, letter_grade, dimension_details, etc.
    """
    profiles = load_profiles(profiles_path)
    profile = profiles[profile_name]
    na_dims = set(profile["na"])

    applicable = {
        d: s for d, s in dimension_scores.items() if d not in na_dims
    }

    weighted_sum = 0.0
    weight_total = 0.0
    dimension_details = {}

    for dim, score in sorted(applicable.items()):
        weight = profile["weights"].get(dim, 1.0)
        weighted_sum += score * weight
        weight_total += 4 * weight  # max possible for this dimension
        dimension_details[dim] = {
            "name": DIMENSION_NAMES[dim],
            "score": score,
            "weight": weight,
            "weighted_contribution": score * weight,
        }

    overall = round((weighted_sum / weight_total * 100) if weight_total else 0, 1)

    if blockers:
        letter = "F"
        capped = True
    else:
        letter = to_letter_grade(overall)
        capped = False

    return {
        "overall_score": overall,
        "letter_grade": letter,
        "capped_by_blocker": capped,
        "profile": profile_name,
        "na_dimensions": sorted(na_dims),
        "dimension_details": dimension_details,
    }


def to_letter_grade(score: float) -> str:
    """Map a 0-100 score to a letter grade."""
    for boundary, grade in GRADE_BOUNDARIES:
        if score >= boundary:
            return grade
    return "F"


def compute_delta(
    current: dict[int, int],
    baseline: dict[int, int] | None,
) -> dict[int, int] | None:
    """Compute per-dimension delta from baseline.

    Returns None if no baseline. Otherwise dict of dim -> delta.
    """
    if baseline is None:
        return None
    return {d: current[d] - baseline.get(d, 0) for d in current}


def build_grade_result(
    dimension_scores: dict[int, int],
    findings: list[dict],
    scan_result: dict,
    profile_name: str,
    profiles_path: Path,
    baseline: dict | None = None,
) -> dict:
    """Build the complete grade.json structure.

    Args:
        dimension_scores: Dict mapping dimension (1-11) to score (0-4).
        findings: List of finding dicts.
        scan_result: Output of scan.py.
        profile_name: Weight profile name.
        profiles_path: Path to profiles.yaml.
        baseline: Previous dimension scores, if any.

    Returns:
        Complete grade result dict suitable for serialisation.
    """
    has_blockers = any(f["severity"] == "blocker" for f in findings)
    score_result = compute_score(
        dimension_scores, profile_name, profiles_path, blockers=has_blockers,
    )
    delta = compute_delta(dimension_scores, baseline)

    return {
        **score_result,
        "dimension_scores": dimension_scores,
        "findings": findings,
        "scan": scan_result,
        "delta": delta,
        "baseline_status": "initial" if baseline is None else "compared",
    }


def load_baseline(skill_path: Path) -> dict | None:
    """Load baseline from .skill-grader/baseline.json if it exists."""
    baseline_file = Path(skill_path) / ".skill-grader" / "baseline.json"
    if not baseline_file.exists():
        return None
    with open(baseline_file, encoding="utf-8") as f:
        data = json.load(f)
    return {int(k): v for k, v in data.get("dimension_scores", {}).items()}


def save_baseline(skill_path: Path, grade_result: dict) -> Path:
    """Save current scores as baseline."""
    baseline_dir = Path(skill_path) / ".skill-grader"
    baseline_dir.mkdir(parents=True, exist_ok=True)
    baseline_file = baseline_dir / "baseline.json"
    with open(baseline_file, "w", encoding="utf-8") as f:
        json.dump({
            "dimension_scores": grade_result["dimension_scores"],
            "overall_score": grade_result["overall_score"],
            "letter_grade": grade_result["letter_grade"],
            "profile": grade_result["profile"],
        }, f, indent=2)
    return baseline_file
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_score.py -v
```

- [ ] **Step 5: Commit**

```bash
git add scripts/score.py tests/test_score.py
git commit -m "feat: add score.py weighted scoring and baseline delta with tests"
```

---

### Task 6: render.py — grade.json to grade.md + grade.html

**Files:**
- Create: `scripts/render.py`
- Create: `assets/report.css.template`
- Create: `assets/report.html.template`
- Create: `tests/test_render.py`

Transforms the grade result dict into readable Markdown and self-contained HTML reports.

- [ ] **Step 1: Write failing tests**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_render.py -v
```

- [ ] **Step 3: Write assets/report.css.template**

CSS for the HTML report. Matches code-audit's typographic identity.

```css
:root {
  --font-mono: 'SF Mono', 'Cascadia Code', 'Fira Code', monospace;
  --font-body: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  --bg: #0d1117;
  --bg-card: #161b22;
  --bg-hover: #1c2129;
  --text: #e6edf3;
  --text-muted: #8b949e;
  --border: #30363d;
  --accent: #58a6ff;
  --severity-blocker: #f85149;
  --severity-major: #d29922;
  --severity-minor: #58a6ff;
  --severity-nit: #8b949e;
  --grade-a: #3fb950;
  --grade-b: #58a6ff;
  --grade-c: #d29922;
  --grade-d: #f0883e;
  --grade-f: #f85149;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: var(--font-body);
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
  padding: 2rem;
  max-width: 960px;
  margin: 0 auto;
}

h1, h2, h3 { font-family: var(--font-mono); font-weight: 600; }
h1 { font-size: 1.75rem; margin-bottom: 1.5rem; }
h2 { font-size: 1.25rem; margin: 2rem 0 1rem; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; }
h3 { font-size: 1rem; margin: 1.5rem 0 0.75rem; }

.score-header {
  display: flex;
  align-items: center;
  gap: 2rem;
  padding: 1.5rem;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 8px;
  margin-bottom: 2rem;
}

.grade-badge {
  font-family: var(--font-mono);
  font-size: 3rem;
  font-weight: 700;
  width: 5rem;
  height: 5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  border: 2px solid;
}

.grade-a { color: var(--grade-a); border-color: var(--grade-a); }
.grade-b { color: var(--grade-b); border-color: var(--grade-b); }
.grade-c { color: var(--grade-c); border-color: var(--grade-c); }
.grade-d { color: var(--grade-d); border-color: var(--grade-d); }
.grade-f { color: var(--grade-f); border-color: var(--grade-f); }

.score-details { flex: 1; }
.score-details .score-number { font-size: 1.25rem; font-weight: 600; }
.score-details .profile { color: var(--text-muted); font-size: 0.875rem; }

.dimension-table { width: 100%; border-collapse: collapse; }
.dimension-table th,
.dimension-table td {
  padding: 0.5rem 0.75rem;
  text-align: left;
  border-bottom: 1px solid var(--border);
  font-size: 0.875rem;
}
.dimension-table th { color: var(--text-muted); font-weight: 500; }
.dimension-table .score-cell { font-family: var(--font-mono); text-align: center; width: 4rem; }
.dimension-table .na { color: var(--text-muted); font-style: italic; }
.dimension-table .delta-pos { color: var(--grade-a); }
.dimension-table .delta-neg { color: var(--grade-f); }

.finding {
  padding: 0.75rem 1rem;
  margin-bottom: 0.5rem;
  background: var(--bg-card);
  border-left: 3px solid;
  border-radius: 0 4px 4px 0;
}
.finding.blocker { border-color: var(--severity-blocker); }
.finding.major { border-color: var(--severity-major); }
.finding.minor { border-color: var(--severity-minor); }
.finding.nit { border-color: var(--severity-nit); }

.finding-header {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  margin-bottom: 0.25rem;
}
.severity-tag {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  padding: 0.125rem 0.5rem;
  border-radius: 3px;
}
.severity-tag.blocker { background: var(--severity-blocker); color: white; }
.severity-tag.major { background: var(--severity-major); color: var(--bg); }
.severity-tag.minor { background: var(--severity-minor); color: var(--bg); }
.severity-tag.nit { background: var(--severity-nit); color: var(--bg); }

.location { font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-muted); }
.problem { margin: 0.25rem 0; }
.suggested-fix { color: var(--text-muted); font-size: 0.85rem; }
.suggested-fix::before { content: "Fix: "; font-weight: 600; }

.meta { color: var(--text-muted); font-size: 0.8rem; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--border); }
```

- [ ] **Step 4: Write assets/report.html.template**

Jinja2 template for single-skill HTML report:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Skill Grade: {{ skill_name }}</title>
<style>
{{ css }}
</style>
</head>
<body>

<h1>Skill Grade: {{ skill_name }}</h1>

<div class="score-header">
  <div class="grade-badge grade-{{ grade_class }}">{{ letter_grade }}</div>
  <div class="score-details">
    <div class="score-number">{{ overall_score }} / 100</div>
    <div class="profile">Profile: {{ profile }}{% if capped_by_blocker %} &mdash; <span style="color: var(--severity-blocker);">capped by blocker</span>{% endif %}</div>
    <div class="profile">{{ baseline_status }}{% if delta_summary %} &mdash; {{ delta_summary }}{% endif %}</div>
  </div>
</div>

<h2>Dimension Scores</h2>
<table class="dimension-table">
<thead>
<tr><th>#</th><th>Dimension</th><th class="score-cell">Score</th><th class="score-cell">Weight</th>{% if has_delta %}<th class="score-cell">Delta</th>{% endif %}</tr>
</thead>
<tbody>
{% for dim in dimensions %}
<tr>
  <td>{{ dim.number }}</td>
  <td>{{ dim.name }}{% if dim.na %} <span class="na">(N/A)</span>{% endif %}</td>
  <td class="score-cell">{% if dim.na %}—{% else %}{{ dim.score }}/4{% endif %}</td>
  <td class="score-cell">{% if dim.na %}—{% else %}{{ dim.weight }}{% endif %}</td>
  {% if has_delta %}<td class="score-cell {% if dim.delta > 0 %}delta-pos{% elif dim.delta < 0 %}delta-neg{% endif %}">{% if dim.na %}—{% elif dim.delta > 0 %}+{{ dim.delta }}{% elif dim.delta < 0 %}{{ dim.delta }}{% elif dim.delta == 0 %}={% else %}—{% endif %}</td>{% endif %}
</tr>
{% endfor %}
</tbody>
</table>

{% if na_dimensions %}
<p style="color: var(--text-muted); font-size: 0.85rem; margin-top: 0.5rem;">
  N/A dimensions ({{ na_dimensions | join(', ') }}) are excluded from the weighted score.
</p>
{% endif %}

<h2>Findings</h2>
{% for severity in severity_order %}
{% if findings_by_severity[severity] %}
<h3>{{ severity | title }} ({{ findings_by_severity[severity] | length }})</h3>
{% for f in findings_by_severity[severity] %}
<div class="finding {{ severity }}">
  <div class="finding-header">
    <span class="severity-tag {{ severity }}">{{ severity }}</span>
    <span class="location">D{{ f.dimension }}: {{ f.dimension_name }}</span>
    {% if f.location %}<span class="location">{{ f.location }}</span>{% endif %}
  </div>
  <div class="problem">{{ f.problem }}</div>
  {% if f.suggested_fix %}<div class="suggested-fix">{{ f.suggested_fix }}</div>{% endif %}
</div>
{% endfor %}
{% endif %}
{% endfor %}

{% if not findings_by_severity.values() | sum(attribute='__len__', start=0) %}
<p style="color: var(--text-muted);">No findings.</p>
{% endif %}

<div class="meta">
  Generated by skill-grader | Profile: {{ profile }} | {{ timestamp }}
</div>

</body>
</html>
```

- [ ] **Step 5: Implement render.py**

```python
"""Render grade results to Markdown and HTML."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Template

from scripts.score import DIMENSION_NAMES

ASSETS_DIR = Path(__file__).parent.parent / "assets"
SEVERITY_ORDER = ["blocker", "major", "minor", "nit"]


def render_markdown(grade_result: dict) -> str:
    """Render grade result as Markdown report."""
    lines = []
    skill_name = Path(grade_result["scan"]["skill_path"]).name
    lines.append(f"# Skill Grade: {skill_name}\n")

    # Score header
    grade = grade_result["letter_grade"]
    score = grade_result["overall_score"]
    profile = grade_result["profile"]
    lines.append(f"**Grade: {grade}** | Score: {score}/100 | Profile: {profile}")

    if grade_result["capped_by_blocker"]:
        lines.append("**Grade capped at F due to blocker findings.**")

    if grade_result["na_dimensions"]:
        na_names = [DIMENSION_NAMES[d] for d in grade_result["na_dimensions"]]
        lines.append(f"N/A dimensions: {', '.join(na_names)}")

    lines.append(f"Baseline: {grade_result['baseline_status']}")
    lines.append("")

    # Dimension table
    lines.append("## Dimension Scores\n")
    has_delta = grade_result.get("delta") is not None
    header = "| # | Dimension | Score | Weight |"
    sep = "|---|-----------|-------|--------|"
    if has_delta:
        header += " Delta |"
        sep += "-------|"
    lines.append(header)
    lines.append(sep)

    na_set = set(grade_result["na_dimensions"])
    details = grade_result.get("dimension_details", {})

    for dim in range(1, 12):
        name = DIMENSION_NAMES[dim]
        if dim in na_set:
            row = f"| {dim} | {name} | N/A | — |"
            if has_delta:
                row += " — |"
        else:
            d = details.get(dim, {})
            s = d.get("score", grade_result["dimension_scores"].get(dim, "?"))
            w = d.get("weight", 1.0)
            row = f"| {dim} | {name} | {s}/4 | {w} |"
            if has_delta:
                delta_val = grade_result["delta"].get(dim, 0)
                if delta_val > 0:
                    row += f" +{delta_val} |"
                elif delta_val < 0:
                    row += f" {delta_val} |"
                else:
                    row += " = |"
        lines.append(row)

    lines.append("")

    # Findings by severity
    lines.append("## Findings\n")
    findings = grade_result.get("findings", [])
    by_severity = {}
    for f in findings:
        sev = f["severity"]
        by_severity.setdefault(sev, []).append(f)

    for sev in SEVERITY_ORDER:
        group = by_severity.get(sev, [])
        if not group:
            continue
        lines.append(f"### {sev.title()} ({len(group)})\n")
        for f in group:
            dim_name = DIMENSION_NAMES.get(f["dimension"], f"D{f['dimension']}")
            loc = f.get("location", "")
            lines.append(f"- **[D{f['dimension']}] {dim_name}**"
                         + (f" `{loc}`" if loc else ""))
            lines.append(f"  {f['problem']}")
            if f.get("suggested_fix"):
                lines.append(f"  *Fix:* {f['suggested_fix']}")
            lines.append("")

    if not findings:
        lines.append("No findings.\n")

    return "\n".join(lines)


def render_html(grade_result: dict) -> str:
    """Render grade result as self-contained HTML report."""
    css_file = ASSETS_DIR / "report.css.template"
    html_file = ASSETS_DIR / "report.html.template"

    css = css_file.read_text(encoding="utf-8")
    template = Template(html_file.read_text(encoding="utf-8"))

    skill_name = Path(grade_result["scan"]["skill_path"]).name
    letter = grade_result["letter_grade"]
    grade_class = letter[0].lower()  # a, b, c, d, f
    has_delta = grade_result.get("delta") is not None
    na_set = set(grade_result["na_dimensions"])
    details = grade_result.get("dimension_details", {})

    dimensions = []
    for dim in range(1, 12):
        d = details.get(dim, {})
        delta_val = grade_result["delta"].get(dim, 0) if has_delta else None
        dimensions.append({
            "number": dim,
            "name": DIMENSION_NAMES[dim],
            "score": d.get("score", grade_result["dimension_scores"].get(dim, 0)),
            "weight": d.get("weight", 1.0),
            "na": dim in na_set,
            "delta": delta_val,
        })

    findings = grade_result.get("findings", [])
    findings_by_severity = {}
    for f in findings:
        f_copy = dict(f)
        f_copy["dimension_name"] = DIMENSION_NAMES.get(f["dimension"], "")
        findings_by_severity.setdefault(f["severity"], []).append(f_copy)

    delta_summary = None
    if has_delta:
        regressions = sum(1 for v in grade_result["delta"].values() if v < 0)
        improvements = sum(1 for v in grade_result["delta"].values() if v > 0)
        parts = []
        if improvements:
            parts.append(f"{improvements} improved")
        if regressions:
            parts.append(f"{regressions} regressed")
        if not parts:
            parts.append("no change")
        delta_summary = ", ".join(parts)

    return template.render(
        skill_name=skill_name,
        css=css,
        letter_grade=letter,
        grade_class=grade_class,
        overall_score=grade_result["overall_score"],
        profile=grade_result["profile"],
        capped_by_blocker=grade_result["capped_by_blocker"],
        baseline_status=grade_result["baseline_status"],
        delta_summary=delta_summary,
        has_delta=has_delta,
        dimensions=dimensions,
        na_dimensions=grade_result["na_dimensions"],
        severity_order=SEVERITY_ORDER,
        findings_by_severity=findings_by_severity,
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
uv run pytest tests/test_render.py -v
```

- [ ] **Step 7: Commit**

```bash
git add scripts/render.py assets/ tests/test_render.py
git commit -m "feat: add render.py with Markdown and HTML report generation"
```

---

### Task 7: emit_issues.py — findings to GitHub-importable format

**Files:**
- Create: `scripts/emit_issues.py`
- Create: `tests/test_emit_issues.py`

- [ ] **Step 1: Write failing tests**

```python
"""Tests for emit_issues.py — GitHub issue export."""

import csv
import hashlib
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
        # nit should be excluded
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_emit_issues.py -v
```

- [ ] **Step 3: Implement emit_issues.py**

```python
"""Convert grade findings to GitHub-importable issue format."""

from __future__ import annotations

import csv
import hashlib
import io
import json

from scripts.score import DIMENSION_NAMES

DIMENSION_SLUGS = {
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


def _fingerprint(skill_name: str, finding: dict) -> str:
    """Stable hash for deduplication across re-runs."""
    parts = [
        skill_name,
        str(finding["dimension"]),
        finding.get("location", ""),
        finding["problem"].strip().lower(),
    ]
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def findings_to_issues(
    findings: list[dict], skill_name: str
) -> list[dict]:
    """Convert findings at major severity and above to issue dicts.

    Returns list of {title, body, labels} dicts.
    """
    issues = []
    for f in findings:
        if f["severity"] not in ("blocker", "major"):
            continue

        dim = f["dimension"]
        dim_name = DIMENSION_NAMES.get(dim, f"Dimension {dim}")
        dim_slug = DIMENSION_SLUGS.get(dim, f"dim-{dim}")
        fp = _fingerprint(skill_name, f)

        title = f"[skill-grader] {skill_name}: D{dim} {dim_name} — {f['problem'][:60]}"

        body_lines = [
            f"**Problem:** {f['problem']}",
            "",
            f"**Location:** `{f.get('location', 'N/A')}`",
            "",
            f"**Suggested fix:** {f.get('suggested_fix', 'N/A')}",
            "",
            f"**Rubric dimension:** D{dim} — {dim_name}",
            "",
            f"<!-- sg:{fp} -->",
        ]

        issues.append({
            "title": title,
            "body": "\n".join(body_lines),
            "labels": [f"severity:{f['severity']}", f"dim:{dim_slug}"],
        })

    return issues


def render_issues_json(issues: list[dict]) -> str:
    """Serialise issues to JSON array string."""
    return json.dumps(issues, indent=2)


def render_issues_csv(issues: list[dict]) -> str:
    """Serialise issues to CSV string."""
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_emit_issues.py -v
```

- [ ] **Step 5: Commit**

```bash
git add scripts/emit_issues.py tests/test_emit_issues.py
git commit -m "feat: add emit_issues.py GitHub issue export with tests"
```

---

### Task 8: Reference documents

**Files:**
- Create: `references/static-checks.md`
- Create: `references/empirical.md`
- Create: `references/issue-import.md`

- [ ] **Step 1: Write references/static-checks.md**

Document which dimensions are mechanically checkable vs. judgment-based. Map scan.py outputs to dimensions. This tells the SKILL.md workflow what the model needs to evaluate vs. what is already measured. Content:

- **Mechanically checkable (scan.py):** D3 (line count), D4 (orphans, dangling refs, duplication), D5 (deterministic prose signals), D6 (caps density), D11 (has_evals)
- **Judgment-required (model):** D1 (description quality), D2 (trigger surface), D5 (which prose should be scripts — confirmation), D6 (rationale quality — beyond caps), D7 (output contract completeness), D8 (example quality), D9 (portability), D10 (safety/intent match)
- **Mixed:** Some dimensions get a floor from mechanical checks and a ceiling from judgment

- [ ] **Step 2: Write references/empirical.md**

Document Mode B delegation. How to call `skill-creator`'s harness for trigger-rate measurement and output-quality comparison. Include the degradation message for non-CC environments.

- [ ] **Step 3: Write references/issue-import.md**

Document the `gh` one-liner for importing issues.json, label setup, and dedup behaviour via fingerprint matching. Content:

```markdown
# Issue Import Guide

## Quick import

    cat issues.json | jq -c '.[]' | while read issue; do
      gh issue create \
        --title "$(echo "$issue" | jq -r '.title')" \
        --body "$(echo "$issue" | jq -r '.body')" \
        --label "$(echo "$issue" | jq -r '.labels | join(",")')"
    done

## Label setup

Create labels before first import:

    for sev in blocker major; do
      gh label create "severity:$sev" --color "$([ "$sev" = blocker ] && echo d73a4a || echo e4e669)"
    done

    for dim in description-triggering trigger-surface progressive-disclosure \
               resource-hygiene script-vs-prose instructional-voice \
               output-contract examples environment-portability \
               least-surprise-safety testability; do
      gh label create "dim:$dim" --color c5def5
    done

## Deduplication

Each issue body contains `<!-- sg:<hash> -->`. Before creating, check:

    gh issue list --state open --json body | jq -r '.[].body' | grep -c 'sg:<hash>'

The import script should skip issues whose fingerprint already appears in an open issue.
```

- [ ] **Step 4: Commit**

```bash
git add references/
git commit -m "docs: add static-checks, empirical, and issue-import references"
```

---

### Task 9: SKILL.md — the skill itself

**Files:**
- Create: `SKILL.md`

The SKILL.md orchestrates the grading workflow. It is a Claude skill that reads a target skill, runs scan.py, auto-detects profile, guides the model through judgment-based scoring, calls score.py, and produces outputs via render.py.

- [ ] **Step 1: Write SKILL.md**

Frontmatter:
```yaml
---
name: skill-grader
description: >
  Grade the quality of a Claude Skill against an 11-dimension rubric.
  Use when asked to grade, review, evaluate, audit, or score a skill.
  Use when asked "is this skill any good?" or "what's wrong with this skill?"
  Do NOT use for general code review, code audit, or non-skill projects.
---
```

Body structure (keep under 300 lines — push detail to references):
1. **Mode selection** — static (default) vs empirical (--empirical, CC only)
2. **Workflow steps:**
   - Run `scan.py <skill-path>` to get mechanical measurements
   - Run `detect_profile.py <skill-path>` to get profile guess (or accept --profile override)
   - Read `references/rubric.md` for anchored descriptors
   - Read `references/static-checks.md` to know which dimensions are pre-measured
   - For each judgment-required dimension: read the skill, score 0-4 against rubric, write a finding for any score < 4
   - For mechanically-informed dimensions: use scan.py output as floor, add judgment-based adjustment
   - Compile all scores and findings
   - Run `score.py` (via Python) to compute weighted score, letter grade, baseline delta
   - Run `render.py` to produce grade.md and grade.html
   - Optionally run `emit_issues.py` if --emit-issues
   - If --set-baseline, save baseline
   - If --empirical, read `references/empirical.md` and delegate to skill-creator
   - If --self, grade this skill under `workflow` profile (fixed, not auto-detected)
3. **Output summary** — what gets produced and where
4. **Rubric summary** — brief table of 11 dimensions (detail in references/rubric.md)

- [ ] **Step 2: Self-review SKILL.md against its own rubric**

Manually check: does the SKILL.md score well on D1 (trigger description), D3 (line count), D4 (resource hygiene), D6 (voice), D7 (output contract), D9 (portability)?

- [ ] **Step 3: Commit**

```bash
git add SKILL.md
git commit -m "feat: add SKILL.md skill workflow"
```

---

### Task 10: Self-grade smoke test

**Files:**
- None created; this is a validation step

- [ ] **Step 1: Run scan.py against skill-grader itself**

```bash
uv run python -c "
from scripts.scan import scan_skill
from pathlib import Path
import json
result = scan_skill(Path('.'))
print(json.dumps(result, indent=2))
"
```

Verify: no orphaned files, no dangling refs, low caps density, has scripts, has evals.

- [ ] **Step 2: Run detect_profile.py against self**

```bash
uv run python -c "
from scripts.detect_profile import detect_profile
from pathlib import Path
import json
result = detect_profile(Path('.'))
print(json.dumps(result, indent=2))
"
```

Verify: detects "workflow" (scripts + tests + artifacts).

- [ ] **Step 3: Run all tests**

```bash
uv run pytest -v
```

Verify: all tests pass.

- [ ] **Step 4: Commit any fixes**

```bash
git add -A
git commit -m "fix: address issues found during self-grade smoke test"
```

---

### Task 11: Install as skill plugin

**Files:**
- Potentially modify: symlink or copy to `~/.claude/skills/skill-grader`

- [ ] **Step 1: Symlink into skills directory**

```bash
ln -sf /Users/mattgreenwood/Code/skill-skill-grader ~/.claude/skills/skill-grader
```

- [ ] **Step 2: Verify skill is discoverable**

Check that `SKILL.md` is at `~/.claude/skills/skill-grader/SKILL.md` and readable.

- [ ] **Step 3: Commit the spec move** (if not already done)

Move the spec to its canonical location per the spec's own convention:

```bash
mv docs/skill-grader-spec.md docs/spec.md
git add docs/
git commit -m "docs: rename spec to canonical docs/spec.md"
```
