"""scan.py — mechanical checks for a skill directory.

Extracts measurements from a skill directory with no model judgment.
All checks are purely mechanical: counts, file graph analysis, pattern matching.
"""

from __future__ import annotations

import re
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CONTENT_EXTENSIONS = {
    ".md", ".py", ".sh", ".yaml", ".yml", ".json", ".html",
    ".css", ".txt", ".template", ".js", ".ts",
}

CAPS_WORDS = re.compile(
    r"\b(MUST|NEVER|ALWAYS|CRITICAL|IMPORTANT|REQUIRED|SHALL|ABSOLUTELY|MANDATORY)\b"
)

EVAL_DIRS = {"tests", "test", "evals", "eval"}

TOC_MARKER = re.compile(r"^\s*-\s*\[.+\]\(#", re.MULTILINE)

DETERMINISTIC_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"count the lines",
        r"check if the file",
        r"scan the directory",
        r"list all files",
        r"measure the length",
        r"calculate the number",
    ]
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _find_bundled_files(skill_path: Path) -> list[str]:
    """Return all content files as relative path strings, excluding dotfiles."""
    result = []
    for p in skill_path.rglob("*"):
        if p.is_file() and p.suffix in CONTENT_EXTENSIONS:
            # Skip dotfiles and paths containing hidden directories
            parts = p.relative_to(skill_path).parts
            if any(part.startswith(".") for part in parts):
                continue
            result.append(str(p.relative_to(skill_path)))
    return sorted(result)


def _collect_md_text(skill_path: Path, bundled: list[str]) -> str:
    """Read all .md and .txt and .yaml files in the skill for ref scanning."""
    texts = []
    for rel in bundled:
        p = skill_path / rel
        if p.suffix in {".md", ".txt", ".yaml", ".yml"}:
            try:
                texts.append(p.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                pass
    return "\n".join(texts)


def _find_referenced_files(
    skill_path: Path, skill_text: str, bundled: list[str]
) -> list[str]:
    """Find files mentioned in SKILL.md or other bundled .md/.txt/.yaml files."""
    # Gather all text from .md, .txt, .yaml files (includes SKILL.md)
    search_text = _collect_md_text(skill_path, bundled)

    bundled_set = set(bundled)
    bundled_names = {Path(b).name: b for b in bundled}

    referenced = set()

    for rel in bundled:
        p = Path(rel)
        name = p.name
        # Check if filename or relative path appears in the combined text
        if name in search_text or rel in search_text:
            referenced.add(rel)
            continue
        # Check path variants (e.g. references/guide.md vs guide.md)
        parts = p.parts
        for i in range(len(parts)):
            variant = "/".join(parts[i:])
            if variant in search_text:
                referenced.add(rel)
                break

    return sorted(referenced)


def _is_instruction_line(line: str, in_code_fence: bool, in_frontmatter: bool) -> bool:
    """Return True if this line should be checked for caps density."""
    stripped = line.strip()
    if in_code_fence or in_frontmatter:
        return False
    if not stripped:
        return False
    if stripped.startswith("#"):  # heading
        return False
    if stripped.startswith("|"):  # table
        return False
    return True


def _measure_caps_density(lines: list[str]) -> tuple[float, list[int]]:
    """Measure fraction of instruction lines containing ALL-CAPS imperative words.

    Returns (density_float, list_of_1-indexed_line_numbers).
    """
    instruction_count = 0
    caps_line_numbers: list[int] = []

    in_code_fence = False
    in_frontmatter = False
    frontmatter_done = False
    frontmatter_lines = 0

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Handle frontmatter
        if i == 1 and stripped == "---":
            in_frontmatter = True
            frontmatter_lines += 1
            continue
        if in_frontmatter:
            frontmatter_lines += 1
            if stripped == "---" and frontmatter_lines > 1:
                in_frontmatter = False
                frontmatter_done = True
            continue

        # Handle code fences
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_fence = not in_code_fence
            continue

        if _is_instruction_line(line, in_code_fence, in_frontmatter):
            instruction_count += 1
            if CAPS_WORDS.search(line):
                caps_line_numbers.append(i)

    if instruction_count == 0:
        return 0.0, []
    density = len(caps_line_numbers) / instruction_count
    return density, caps_line_numbers


def _find_large_refs_without_toc(skill_path: Path) -> list[str]:
    """Return reference .md files over 300 lines lacking a TOC marker."""
    result = []
    refs_dir = skill_path / "references"
    if not refs_dir.exists():
        return result
    for p in refs_dir.rglob("*.md"):
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        lines = text.splitlines()
        if len(lines) > 300 and not TOC_MARKER.search(text):
            result.append(str(p.relative_to(skill_path)))
    return sorted(result)


def _has_evals(skill_path: Path) -> bool:
    """Check for tests/, test/, evals/, eval/ directories with files."""
    for dir_name in EVAL_DIRS:
        d = skill_path / dir_name
        if d.is_dir():
            for p in d.rglob("*"):
                if p.is_file():
                    return True
    return False


def _extract_paragraphs(text: str) -> list[str]:
    """Split text into normalised paragraph blocks, skipping code fences."""
    paragraphs = []
    in_code_fence = False
    current: list[str] = []

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_fence = not in_code_fence
            if current:
                block = " ".join(current).strip()
                if len(block) >= 80:
                    paragraphs.append(block)
                current = []
            continue
        if in_code_fence:
            continue
        if stripped:
            current.append(stripped)
        else:
            if current:
                block = " ".join(current).strip()
                if len(block) >= 80:
                    paragraphs.append(block)
                current = []

    if current:
        block = " ".join(current).strip()
        if len(block) >= 80:
            paragraphs.append(block)

    return paragraphs


def _normalise_paragraph(para: str) -> str:
    """Normalise whitespace for comparison."""
    return re.sub(r"\s+", " ", para).strip().lower()


def _find_duplicated_blocks(
    skill_path: Path, skill_text: str, bundled: list[str]
) -> list[str]:
    """Find paragraphs (80+ chars) duplicated between SKILL.md and reference .md files."""
    skill_paras = set(_normalise_paragraph(p) for p in _extract_paragraphs(skill_text))

    duplicated = []
    for rel in bundled:
        p = skill_path / rel
        if p.name == "SKILL.md" or p.suffix != ".md":
            continue
        try:
            ref_text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for para in _extract_paragraphs(ref_text):
            norm = _normalise_paragraph(para)
            if norm in skill_paras and len(norm) >= 80:
                duplicated.append(norm[:120])

    # Deduplicate
    seen: set[str] = set()
    result = []
    for d in duplicated:
        if d not in seen:
            seen.add(d)
            result.append(d)
    return result


def _find_deterministic_prose(lines: list[str]) -> list[str]:
    """Find lines matching deterministic/mechanical prose patterns."""
    matches = []
    for line in lines:
        for pattern in DETERMINISTIC_PATTERNS:
            if pattern.search(line):
                matches.append(line.strip())
                break
    return matches


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def scan_skill(skill_path: Path) -> dict:
    """Scan a skill directory and return a dict of mechanical measurements."""
    skill_path = Path(skill_path)
    skill_md = skill_path / "SKILL.md"

    # Read SKILL.md
    if skill_md.exists():
        skill_text = skill_md.read_text(encoding="utf-8", errors="replace")
    else:
        skill_text = ""

    skill_lines = skill_text.splitlines()
    skill_md_lines = len(skill_lines)

    # Bundled files
    bundled = _find_bundled_files(skill_path)

    # Referenced files
    referenced = _find_referenced_files(skill_path, skill_text, bundled)

    # Orphaned files: bundled but not referenced (excluding SKILL.md itself)
    referenced_set = set(referenced)
    orphaned = [
        b for b in bundled
        if b not in referenced_set and Path(b).name != "SKILL.md"
    ]

    # Dangling refs: referenced but not bundled
    bundled_set = set(bundled)
    dangling = [r for r in referenced if r not in bundled_set]

    # Caps density
    caps_density, caps_lines = _measure_caps_density(skill_lines)

    # Large refs without TOC
    large_refs_without_toc = _find_large_refs_without_toc(skill_path)

    # Has scripts
    scripts_dir = skill_path / "scripts"
    has_scripts = scripts_dir.is_dir() and any(
        p.is_file() for p in scripts_dir.rglob("*")
        if not p.name.startswith(".")
    )

    # Has evals
    has_evals = _has_evals(skill_path)

    # Duplicated blocks
    duplicated_blocks = _find_duplicated_blocks(skill_path, skill_text, bundled)

    # Deterministic prose signals
    deterministic_prose_signals = _find_deterministic_prose(skill_lines)

    return {
        "skill_path": str(skill_path.resolve()),
        "skill_md_lines": skill_md_lines,
        "orphaned_files": orphaned,
        "dangling_refs": dangling,
        "caps_density": caps_density,
        "caps_lines": caps_lines,
        "large_refs_without_toc": large_refs_without_toc,
        "has_scripts": has_scripts,
        "has_evals": has_evals,
        "duplicated_blocks": duplicated_blocks,
        "bundled_files": bundled,
        "referenced_files": referenced,
        "deterministic_prose_signals": deterministic_prose_signals,
    }
