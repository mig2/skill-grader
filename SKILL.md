---
name: skill-grader
description: >
  Grade the quality of a Claude Skill against a 12-dimension rubric.
  Use when asked to grade, review, evaluate, audit, or score a skill.
  Use when asked "is this skill any good?" or "what's wrong with this skill?"
  Use when asked to check skill quality, assess a skill, or run skill-grader.
  Do NOT use for general code review, code audit, or non-skill projects.
  Do NOT use for authoring or rewriting skills — this tool produces findings only.
---

## Purpose

skill-grader evaluates a Claude Skill against a 12-dimension rubric and produces a structured grade report. For repo layout, install instructions, and background, see `README.md`. It measures description quality, trigger coverage, structural hygiene, scripting discipline, voice, output contracts, examples, portability, safety, script correctness, and behavioral evals. It does not rewrite, fix, or author skills — it diagnoses them. Use the findings as input to a revision pass, not as a rewrite directive.

---

## Mode Selection

- **Static (default):** Reads SKILL.md and bundled resources. No skill execution. Works in any environment.
- **Empirical (`--empirical`):** Adds behavioral measurement — trigger-rate sampling and output-quality probing. Requires the Claude CLI with skill-creator available.
- If `--empirical` is requested in an unsupported environment, degrade to static and state explicitly: "Empirical mode unavailable — running static only."

---

## Invocation

```
skill-grader <path-to-skill>              # single skill, static mode
skill-grader <path> --empirical           # adds empirical measurement (CC only)
skill-grader <dir> --batch                # discovers */SKILL.md, grades each
skill-grader <path> --set-baseline        # grade and save result as baseline
skill-grader <path> --profile style       # override auto-detected profile
skill-grader <path> --emit-issues         # adds issues.json + issues.csv output
skill-grader --self                       # grade this skill under the workflow profile
```

---

## Workflow

### Step 1: Run mechanical scan

```bash
uv run python scripts/scan.py <skill-path>
```

Read the scan result JSON. It provides measurements for dimensions 3 (progressive disclosure), 4 (resource hygiene), 5 (script vs. prose), 6 (instructional voice), 11 (script correctness), and 12 (behavioral evals). Treat these as floors — mechanical checks can only confirm presence, not quality.

### Step 2: Detect or accept profile

```bash
uv run python scripts/detect_profile.py <skill-path>
```

Use the detected profile unless `--profile` was specified. The profile controls which rubric anchors apply and which dimensions are weighted. State the profile in the report header so readers know which lens was applied.

### Step 3: Read references

- Read `references/rubric.md` — anchored 0–4 descriptors for all 12 dimensions.
- Read `references/static-checks.md` — which dimensions are mechanical vs. judgment, and what each check covers.

Do not proceed to scoring without reading these. The anchors are the ground truth; do not substitute your own heuristics.

### Step 4: Score each dimension

For each of the 12 dimensions:

- **Mechanically checked dimensions:** Use the scan result as the floor. Adjust upward only if judgment finds additional quality beyond what the scan can measure.
- **Judgment-required dimensions:** Read the skill, compare against the rubric descriptors, and assign a score of 0–4.
- **Dimension 10 (Least Surprise / Safety):** Any intent mismatch or undisclosed side-effect is an automatic **blocker**, regardless of score.

Write a finding for every score below 4:

| Score | Severity |
|-------|----------|
| 0–1 on any dimension | major |
| 2 on any dimension | minor |
| 3 on any dimension | nit |
| Dimension 10 intent mismatch | blocker (regardless of score) |

Each finding must include: dimension number, severity, location (file + line or section), problem description, and a concrete fix suggestion.

### Step 5: Compute grade

Pass dimension scores, findings, the scan result, and the detected profile to `score.py`'s `build_grade_result()`. If a baseline exists for this skill, load it with `load_baseline()` and pass it to `build_grade_result()` to compute score deltas.

### Step 6: Render outputs

- Always render `grade.md` and `grade.html` via `render.py`'s `render_markdown()` and `render_html()`.
- Always write `grade.json` — it is the machine-readable artifact for baselining and CI gating.
- If `--emit-issues`: render `issues.json` and `issues.csv` via `emit_issues.py`. See `references/issue-import.md` for schema details.
- If `--set-baseline`: save the current result as the new baseline via `score.py`'s `save_baseline()`.

### Step 7: Empirical measurement (--empirical only)

Read `references/empirical.md` before proceeding. Check that the Claude CLI and skill-creator are available. If available, delegate trigger-rate sampling and output-quality measurement per the protocol in that reference. If unavailable, note the degradation in the report and continue with static results only.

### Step 8: Self-grade (--self only)

Grade this skill (skill-grader's own SKILL.md) under the `workflow` profile — fixed, not auto-detected. A grading skill that cannot score well on its own criteria is not credible. Treat the self-grade result as a required smoke test.

---

## Rubric Summary

Full anchored descriptors are in `references/rubric.md`. This table is a navigation aid only.

| # | Dimension | What it checks |
|---|-----------|----------------|
| 1 | Description Triggering | What + when stated? Trigger phrases present? Negative scope declared? |
| 2 | Trigger Surface Coverage | Realistic phrasings? Oblique requests? Sibling skill collisions? |
| 3 | Progressive Disclosure | SKILL.md within ~500 lines? Detail delegated to references/? |
| 4 | Resource Hygiene | No orphan files, no dangling references, no duplication? |
| 5 | Script vs. Prose | Deterministic work scripted, not described in prose? |
| 6 | Instructional Voice | Imperative? Rationale over mandate? Low ALL-CAPS density? |
| 7 | Output Contract | Format pinned to template or schema? Reader knows what to expect? |
| 8 | Examples | Present, generalising, not overfit to a single case? |
| 9 | Environment Portability | Assumptions declared? Degradation paths for missing tools? |
| 10 | Least Surprise / Safety | Intent match? No undisclosed side-effects? Gating for destructive ops? |
| 11 | Script Correctness | Bundled scripts covered by unit tests? **N/A when no `scripts/`** |
| 12 | Behavioral Evals | Trigger and quality evals present? Assertions appropriate to the output type? Never N/A |

---

## Outputs

| File | When produced | Purpose |
|------|---------------|---------|
| `grade.md` | Always | Default artifact — human-readable report |
| `grade.html` | Always | Self-contained publication-quality report |
| `grade.json` | Always | Machine-readable result for CI gating and baselines |
| `issues.json` | `--emit-issues` only | Structured issue list for import. See `references/issue-import.md` |
| `issues.csv` | `--emit-issues` only | Spreadsheet-compatible issue list |

---

## Evals

This skill is graded by its own D12, so it ships evals:

- `evals/trigger_eval.json` — queries that should and should not invoke skill-grader. The negative cases cover the sibling collision with `code-audit` and requests to *fix* rather than *diagnose*.
- `evals/evals.json` — task prompts with assertions, graded against the fixtures in `tests/fixtures/` so expected outcomes are known.

Assertions here are objective because the output is objective: a grade, a set of dimension scores, and findings. Do not add assertions of this kind when grading a skill whose output is prose or design — judge those qualitatively instead.
