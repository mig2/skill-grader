"""Render grade result dicts into Markdown and self-contained HTML reports."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from scripts.score import DIMENSION_NAMES

ASSETS_DIR = Path(__file__).parent.parent / "assets"
SEVERITY_ORDER = ["blocker", "major", "minor", "nit"]

# A grade is uninterpretable without knowing what was graded. An installed
# skill and its source repo are different objects and score differently.
MODE_NOTES = {
    "installed": (
        "Evaluating the installed skill. D11 (Testability) reflects what "
        "ships — for full coverage, grade the source codebase."
    ),
    "codebase": (
        "Evaluating the skill codebase. Repo furniture (docs/, README) is "
        "excluded from resource-hygiene checks — for the deployed surface, "
        "grade the installed skill."
    ),
}


def _get_flex(d: dict, key: int):
    """Look up by int key first, then str — handles JSON round-trip."""
    if key in d:
        return d[key]
    return d.get(str(key))


def _format_delta(value: int | float | None) -> str:
    """Format a delta value with sign."""
    if value is None:
        return ""
    if value > 0:
        return f"+{value}"
    return str(value)


def render_markdown(grade_result: dict) -> str:
    """Render a grade result dict as a Markdown string."""
    overall = grade_result["overall_score"]
    letter = grade_result["letter_grade"]
    profile = grade_result.get("profile", "unknown")
    capped = grade_result.get("capped_by_blocker", False)
    na_dims = grade_result.get("na_dimensions") or []
    delta = grade_result.get("delta")
    baseline_status = grade_result.get("baseline_status", "initial")
    dimension_details = grade_result.get("dimension_details") or {}
    dimension_scores = grade_result.get("dimension_scores") or {}
    findings = grade_result.get("findings") or []
    scan = grade_result.get("scan") or grade_result.get("scan_result") or {}
    mode_note = MODE_NOTES.get(scan.get("mode", ""))

    lines: list[str] = []

    # Score header
    lines.append(f"# Skill Grade Report")
    lines.append("")
    lines.append(f"**Grade:** {letter}  |  **Score:** {overall} / 100  |  **Profile:** {profile}")
    lines.append("")

    if mode_note:
        lines.append(f"> {mode_note}")
        lines.append("")

    if capped:
        lines.append("> **Warning:** Grade capped by blocker finding.")
        lines.append("")

    if na_dims:
        na_names = ", ".join(
            f"{n} ({DIMENSION_NAMES.get(n, '?')})" for n in sorted(na_dims)
        )
        lines.append(f"**N/A Dimensions:** {na_names}")
        lines.append("")

    if baseline_status == "compared" and delta is not None:
        regressions = sum(1 for v in delta.values() if v < 0)
        improvements = sum(1 for v in delta.values() if v > 0)
        parts = []
        if improvements:
            parts.append(f"{improvements} improved")
        if regressions:
            parts.append(f"{regressions} regression(s)")
        if not parts:
            parts.append("no change")
        lines.append(f"**Delta vs baseline:** {', '.join(parts)}")
        lines.append("")

    # Dimension table
    lines.append("## Dimension Scores")
    lines.append("")

    has_delta_col = delta is not None

    if has_delta_col:
        lines.append("| # | Dimension | Score | Weight | Delta |")
        lines.append("|---|-----------|-------|--------|-------|")
    else:
        lines.append("| # | Dimension | Score | Weight |")
        lines.append("|---|-----------|-------|--------|")

    for dim_num in range(1, 12):
        name = DIMENSION_NAMES.get(dim_num, f"Dim {dim_num}")
        is_na = dim_num in na_dims

        if is_na:
            score_cell = "N/A"
            weight_cell = "—"
        else:
            detail = _get_flex(dimension_details, dim_num) or {}
            score = detail.get("score") if detail else (_get_flex(dimension_scores, dim_num) or "?")
            weight = detail.get("weight", 1.0) if detail else 1.0
            score_cell = f"{score} / 4"
            weight_cell = str(weight)

        if has_delta_col:
            delta_val = _get_flex(delta, dim_num) if delta else None
            delta_cell = _format_delta(delta_val) if delta_val is not None else "—"
            lines.append(f"| {dim_num} | {name} | {score_cell} | {weight_cell} | {delta_cell} |")
        else:
            lines.append(f"| {dim_num} | {name} | {score_cell} | {weight_cell} |")

    lines.append("")

    # Findings grouped by severity
    if findings:
        lines.append("## Findings")
        lines.append("")

        # Group by severity in order
        by_severity: dict[str, list[dict]] = {sev: [] for sev in SEVERITY_ORDER}
        for f in findings:
            sev = f.get("severity", "nit")
            if sev in by_severity:
                by_severity[sev].append(f)
            else:
                by_severity.setdefault(sev, []).append(f)

        for sev in SEVERITY_ORDER:
            group = by_severity.get(sev, [])
            if not group:
                continue
            lines.append(f"### {sev.upper()}")
            lines.append("")
            for f in group:
                dim_num = f.get("dimension")
                dim_name = DIMENSION_NAMES.get(dim_num, f"Dim {dim_num}") if dim_num else "Unknown"
                location = f.get("location", "")
                problem = f.get("problem", "")
                fix = f.get("suggested_fix", "")

                lines.append(f"**[{sev}]** Dim {dim_num} — {dim_name}")
                if location:
                    lines.append(f"*Location:* `{location}`")
                if problem:
                    lines.append(f"*Problem:* {problem}")
                if fix:
                    lines.append(f"*Fix:* {fix}")
                lines.append("")

    # Delta dimension detail if present
    if has_delta_col and delta:
        lines.append("## Delta Details")
        lines.append("")
        for dim_num, val in sorted(delta.items()):
            if val != 0:
                name = DIMENSION_NAMES.get(dim_num, f"Dim {dim_num}")
                sign = f"+{val}" if val > 0 else str(val)
                lines.append(f"- Dim {dim_num} ({name}): {sign}")
        lines.append("")

    return "\n".join(lines)


def render_html(grade_result: dict) -> str:
    """Render a grade result dict as a self-contained HTML string."""
    overall = grade_result["overall_score"]
    letter = grade_result["letter_grade"]
    profile = grade_result.get("profile", "unknown")
    capped = grade_result.get("capped_by_blocker", False)
    na_dims = set(grade_result.get("na_dimensions") or [])
    delta = grade_result.get("delta")
    baseline_status = grade_result.get("baseline_status", "initial")
    dimension_details = grade_result.get("dimension_details") or {}
    dimension_scores = grade_result.get("dimension_scores") or {}
    findings = grade_result.get("findings") or []
    scan = grade_result.get("scan") or grade_result.get("scan_result") or {}

    mode_note = MODE_NOTES.get(scan.get("mode", ""))

    # grade_class: first letter of grade, lowercased (handles A+, B-, etc.)
    grade_class = letter[0].lower()

    # Read CSS
    css_path = ASSETS_DIR / "report.css.template"
    css = css_path.read_text(encoding="utf-8")

    # Skill name from scan or fallback
    skill_path = scan.get("skill_path", "")
    skill_name = Path(skill_path).resolve().name if skill_path else "Unknown Skill"
    if not skill_name:
        skill_name = "Unknown Skill"

    # Build dimensions list
    has_delta = delta is not None
    dimensions = []
    for dim_num in range(1, 12):
        name = DIMENSION_NAMES.get(dim_num, f"Dim {dim_num}")
        is_na = dim_num in na_dims
        # Keys may be int or str after JSON round-trip
        detail = _get_flex(dimension_details, dim_num) or {}
        score = detail.get("score") if detail else _get_flex(dimension_scores, dim_num)
        weight = detail.get("weight", 1.0) if detail else 1.0
        delta_val = _get_flex(delta, dim_num) if delta else None
        dimensions.append({
            "number": dim_num,
            "name": name,
            "score": score,
            "weight": weight,
            "na": is_na,
            "delta": delta_val,
        })

    # Build findings_by_severity dict
    findings_by_severity: dict[str, list[dict]] = {sev: [] for sev in SEVERITY_ORDER}
    for f in findings:
        sev = f.get("severity", "nit")
        dim_num = f.get("dimension")
        enriched = dict(f)
        enriched["dimension_name"] = DIMENSION_NAMES.get(dim_num, f"Dim {dim_num}") if dim_num else "Unknown"
        if sev in findings_by_severity:
            findings_by_severity[sev].append(enriched)
        else:
            findings_by_severity.setdefault(sev, []).append(enriched)

    # Delta summary string
    delta_summary = ""
    if has_delta and delta:
        regressions = sum(1 for v in delta.values() if v < 0)
        improvements = sum(1 for v in delta.values() if v > 0)
        parts = []
        if improvements:
            parts.append(f"+{improvements} improved")
        if regressions:
            parts.append(f"{regressions} regression(s)")
        if not parts:
            parts.append("no change vs baseline")
        delta_summary = ", ".join(parts)

    # Timestamp
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Render Jinja2 template
    env = Environment(
        loader=FileSystemLoader(str(ASSETS_DIR)),
        autoescape=True,
    )
    template = env.get_template("report.html.template")
    html = template.render(
        skill_name=skill_name,
        css=css,
        mode_note=mode_note,
        letter_grade=letter,
        grade_class=grade_class,
        overall_score=overall,
        profile=profile,
        capped_by_blocker=capped,
        baseline_status=baseline_status,
        delta_summary=delta_summary,
        has_delta=has_delta,
        dimensions=dimensions,
        na_dimensions=na_dims,
        severity_order=SEVERITY_ORDER,
        findings_by_severity=findings_by_severity,
        timestamp=timestamp,
    )
    return html
