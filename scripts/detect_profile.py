"""detect_profile.py — archetype heuristic for skill classification.

Analyses a skill's structure to guess which weight profile applies:
  - workflow:   has scripts + tests/artifacts, procedural instructions
  - reference:  reference dir, declarative content, lookup-oriented
  - style:      no scripts, declarative/convention-heavy rules
  - balanced:   fallback when signals are mixed or weak
"""

from __future__ import annotations

import re
from pathlib import Path


# ---------------------------------------------------------------------------
# Signal patterns
# ---------------------------------------------------------------------------

# Procedural: numbered steps, checklists, action verbs
_PROCEDURAL_PATTERNS = [
    re.compile(r"^\s*\d+\.\s", re.MULTILINE),           # numbered steps
    re.compile(r"^\s*-\s*\[[ x]\]", re.MULTILINE),      # checklists
    re.compile(r"\b(run|execute|call|invoke)\b", re.IGNORECASE),
]

# Declarative: style/voice/tone, conventions/rules, always/never patterns
_DECLARATIVE_PATTERNS = [
    re.compile(r"\b(style|format|voice|tone)\b", re.IGNORECASE),
    re.compile(r"\b(convention|rule|guideline|principle)\b", re.IGNORECASE),
    re.compile(r"\b(always|never|prefer|avoid)\b", re.IGNORECASE),
]

# Artifact: output/emit/produce/generate, file extensions
_ARTIFACT_PATTERNS = [
    re.compile(r"\b(output|emit|produce|generate|render)\b", re.IGNORECASE),
    re.compile(r"\.(json|html|md|csv|yaml)\b", re.IGNORECASE),
]

# Reference: lookup/consult language, knowledge/domain language
_REFERENCE_PATTERNS = [
    re.compile(r"\b(reference|lookup|look up|consult|see.also)\b", re.IGNORECASE),
    re.compile(r"\b(knowledge|domain|context|background)\b", re.IGNORECASE),
]


def _count_pattern_matches(text: str, patterns: list[re.Pattern]) -> int:
    """Count total matches across all patterns in text."""
    total = 0
    for pattern in patterns:
        total += len(pattern.findall(text))
    return total


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_profile(skill_path: Path) -> dict:
    """Analyse a skill directory and return the best-fit weight profile.

    Returns a dict with keys:
      - profile:   "workflow" | "reference" | "style" | "balanced"
      - reasoning: human-readable explanation
      - signals:   dict of raw signal values used for classification
    """
    skill_path = Path(skill_path)

    # --- Gather structural signals ---
    scripts_dir = skill_path / "scripts"
    has_scripts = scripts_dir.is_dir() and any(
        p.is_file() for p in scripts_dir.rglob("*")
        if not p.name.startswith(".")
    )

    tests_dirs = ["tests", "test", "evals", "eval"]
    has_tests = any(
        (skill_path / d).is_dir() and any(
            p.is_file() for p in (skill_path / d).rglob("*")
        )
        for d in tests_dirs
    )

    references_dir = skill_path / "references"
    has_references = references_dir.is_dir() and any(
        p.is_file() for p in references_dir.rglob("*")
    )

    # --- Read all text content ---
    texts: list[str] = []
    skill_md = skill_path / "SKILL.md"
    if skill_md.exists():
        texts.append(skill_md.read_text(encoding="utf-8", errors="replace"))

    # Also read bundled .md files for richer signal
    for p in skill_path.rglob("*.md"):
        if p != skill_md:
            try:
                texts.append(p.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                pass

    combined_text = "\n".join(texts)
    line_count = len(combined_text.splitlines())

    # --- Count content signals ---
    procedural_signals = _count_pattern_matches(combined_text, _PROCEDURAL_PATTERNS)
    declarative_signals = _count_pattern_matches(combined_text, _DECLARATIVE_PATTERNS)
    artifact_signals = _count_pattern_matches(combined_text, _ARTIFACT_PATTERNS)
    reference_signals = _count_pattern_matches(combined_text, _REFERENCE_PATTERNS)

    signals = {
        "has_scripts": has_scripts,
        "has_tests": has_tests,
        "has_references": has_references,
        "procedural_signals": procedural_signals,
        "declarative_signals": declarative_signals,
        "artifact_signals": artifact_signals,
        "reference_signals": reference_signals,
        "line_count": line_count,
    }

    # --- Classify ---
    profile, reasoning = _classify(signals)

    return {
        "profile": profile,
        "reasoning": reasoning,
        "signals": signals,
    }


def _classify(signals: dict) -> tuple[str, str]:
    """Apply classification rules and return (profile, reasoning)."""
    has_scripts = signals["has_scripts"]
    has_tests = signals["has_tests"]
    has_references = signals["has_references"]
    procedural = signals["procedural_signals"]
    declarative = signals["declarative_signals"]
    artifact = signals["artifact_signals"]
    reference = signals["reference_signals"]

    # workflow: has scripts AND (has tests OR artifact signals > 5),
    #           OR has scripts AND procedural > declarative
    if has_scripts and (has_tests or artifact > 5):
        return (
            "workflow",
            "Has scripts directory and either tests or strong artifact signals — "
            "indicates an executable, multi-step workflow skill.",
        )

    if has_scripts and procedural > declarative:
        return (
            "workflow",
            "Has scripts and procedural signals outweigh declarative signals — "
            "indicates a procedural workflow skill without formal tests.",
        )

    # reference: reference signals > 5 AND has references dir AND procedural < declarative
    if reference > 5 and has_references and procedural < declarative:
        return (
            "reference",
            "Strong reference/lookup signals with a references directory and more "
            "declarative than procedural content — indicates a knowledge-lookup skill.",
        )

    # style: no scripts AND declarative > procedural AND declarative > 3
    if not has_scripts and declarative > procedural and declarative > 3:
        return (
            "style",
            "No scripts, declarative signals dominate — indicates a style/convention "
            "skill focused on rules and guidelines rather than execution.",
        )

    # fallback
    return (
        "balanced",
        "Signals are mixed or weak — no single archetype dominates, "
        "so a balanced profile is applied.",
    )
