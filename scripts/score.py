"""Weighted scoring, letter grades, and baseline delta for skill grader."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

# Maps dimension numbers to human-readable names
DIMENSION_NAMES = {
    1: "scope clarity",
    2: "trigger surface coverage",
    3: "progressive disclosure",
    4: "resource hygiene",
    5: "script vs prose",
    6: "instructional voice",
    7: "output contract",
    8: "examples",
    9: "error handling",
    10: "metadata quality",
    11: "testability",
}

# (minimum_score, grade) — checked in order, first match wins
GRADE_BOUNDARIES: list[tuple[float, str]] = [
    (97, "A+"),
    (93, "A"),
    (90, "A-"),
    (87, "B+"),
    (83, "B"),
    (80, "B-"),
    (77, "C+"),
    (73, "C"),
    (70, "C-"),
    (67, "D+"),
    (63, "D"),
    (60, "D-"),
    (0, "F"),
]


def load_profiles(profiles_path: Path) -> dict:
    """Load profiles from YAML, converting dimension keys to int."""
    with open(profiles_path) as f:
        data = yaml.safe_load(f)

    profiles = {}
    for name, cfg in data["profiles"].items():
        profile: dict[str, Any] = {
            "description": cfg.get("description", ""),
            "weights": {},
            "na": [],
        }
        # Convert weight keys to int
        for k, v in (cfg.get("weights") or {}).items():
            profile["weights"][int(k)] = float(v)
        # Convert NA dimension keys to int
        for k in cfg.get("na") or []:
            profile["na"].append(int(k))
        profiles[name] = profile

    return profiles


def to_letter_grade(score: float) -> str:
    """Map 0-100 score to a letter grade using GRADE_BOUNDARIES."""
    for threshold, grade in GRADE_BOUNDARIES:
        if score >= threshold:
            return grade
    return "F"


def compute_score(
    dimension_scores: dict[int, int | float],
    profile_name: str,
    profiles_path: Path,
    *,
    blockers: bool = False,
) -> dict:
    """Compute overall score (0-100), letter grade, and metadata.

    Applies profile weights, excludes N/A dimensions, normalises to 0-100.
    If blockers=True, caps the letter grade at F regardless of numeric score.
    """
    profiles = load_profiles(profiles_path)
    profile = profiles[profile_name]
    weights = profile["weights"]
    na_dims = set(profile["na"])

    # Build applicable dimension list
    applicable = {
        dim: score
        for dim, score in dimension_scores.items()
        if dim not in na_dims
    }

    if not applicable:
        overall = 0.0
    else:
        weighted_sum = 0.0
        weight_total = 0.0
        for dim, score in applicable.items():
            w = weights.get(dim, 1.0)
            weighted_sum += score * w
            weight_total += w

        # Max possible score per dimension is 4
        max_possible = weight_total * 4
        overall = round((weighted_sum / max_possible) * 100, 4) if max_possible else 0.0

    if blockers:
        letter = "F"
    else:
        letter = to_letter_grade(overall)

    return {
        "overall_score": overall,
        "letter_grade": letter,
        "na_dimensions": sorted(na_dims),
        "capped_by_blocker": blockers,
        "profile": profile_name,
        "dimension_scores": dimension_scores,
    }


def compute_delta(
    current: dict[int, int | float],
    baseline: dict[int, int | float] | None,
) -> dict[int, int | float] | None:
    """Compute per-dimension delta versus baseline. Returns None if no baseline."""
    if baseline is None:
        return None
    return {dim: current[dim] - baseline[dim] for dim in current if dim in baseline}


def build_grade_result(
    dimension_scores: dict[int, int | float],
    findings: list[dict],
    scan_result: dict,
    profile_name: str,
    profiles_path: Path,
    baseline: dict | None = None,
) -> dict:
    """Build the complete grade.json structure."""
    has_blockers = any(f.get("severity") == "blocker" for f in (findings or []))
    score_result = compute_score(
        dimension_scores, profile_name, profiles_path, blockers=has_blockers
    )

    baseline_scores = baseline.get("dimension_scores") if baseline else None
    delta = compute_delta(dimension_scores, baseline_scores)

    return {
        **score_result,
        "findings": findings,
        "scan_result": scan_result,
        "baseline_delta": delta,
    }


def load_baseline(skill_path: Path) -> dict | None:
    """Load baseline from <skill_path>/.skill-grader/baseline.json."""
    baseline_file = skill_path / ".skill-grader" / "baseline.json"
    if not baseline_file.exists():
        return None
    with open(baseline_file) as f:
        return json.load(f)


def save_baseline(skill_path: Path, grade_result: dict) -> Path:
    """Save grade_result to <skill_path>/.skill-grader/baseline.json."""
    baseline_dir = skill_path / ".skill-grader"
    baseline_dir.mkdir(parents=True, exist_ok=True)
    baseline_file = baseline_dir / "baseline.json"
    with open(baseline_file, "w") as f:
        json.dump(grade_result, f, indent=2)
    return baseline_file
