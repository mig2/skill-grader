"""Weighted scoring, letter grades, and baseline delta for skill grader."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

# Maps dimension numbers to human-readable names
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
    11: "Script Correctness",
    12: "Behavioral Evals",
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
    extra_na: list[int] | None = None,
) -> dict:
    """Compute overall score (0-100), letter grade, and metadata.

    Applies profile weights, excludes N/A dimensions, normalises to 0-100.
    If blockers=True, caps the letter grade at F regardless of numeric score.

    extra_na marks dimensions unscoreable for this target rather than for this
    archetype — used when the target cannot supply the evidence at all, which
    is a different claim from the skill lacking it.
    """
    profiles = load_profiles(profiles_path)
    profile = profiles[profile_name]
    weights = profile["weights"]
    na_dims = set(profile["na"]) | set(extra_na or [])

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

    # Per-dimension breakdown. Without this the report cannot show the weight
    # actually applied, and silently prints the 1.0 default for every row —
    # which makes a weighted profile indistinguishable from a flat one.
    dimension_details = {
        dim: {
            "name": DIMENSION_NAMES.get(dim, f"Dim {dim}"),
            "score": score,
            "weight": weights.get(dim, 1.0),
            "weighted_contribution": score * weights.get(dim, 1.0),
        }
        for dim, score in sorted(applicable.items())
    }

    return {
        "overall_score": overall,
        "letter_grade": letter,
        "na_dimensions": sorted(na_dims),
        "capped_by_blocker": blockers,
        "profile": profile_name,
        "dimension_scores": dimension_scores,
        "dimension_details": dimension_details,
    }


def compute_delta(
    current: dict[int, int | float],
    baseline: dict[int, int | float] | None,
) -> dict[int, int | float] | None:
    """Compute per-dimension delta versus baseline. Returns None if no baseline."""
    if baseline is None:
        return None
    return {dim: current[dim] - baseline[dim] for dim in current if dim in baseline}


# Verification surfaces an install payload cannot carry. Neither tests/ nor
# evals/ is read at runtime, so no well-built skill ships them — scoring these
# 0 on an installed target would penalise every skill identically, which is a
# constant rather than a measurement.
INSTALLED_UNSCOREABLE = [11, 12]


def unscoreable_dimensions(scan_result: dict | None) -> list[int]:
    """Dimensions the target cannot supply evidence for, whatever the skill.

    Distinct from a profile's N/A list, which says a dimension does not apply
    to this *archetype*. This says the evidence is not present in this *copy*.
    """
    if not scan_result or scan_result.get("mode") != "installed":
        return []
    return list(INSTALLED_UNSCOREABLE)


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
        dimension_scores, profile_name, profiles_path,
        blockers=has_blockers,
        extra_na=unscoreable_dimensions(scan_result),
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
