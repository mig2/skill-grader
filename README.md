# skill-grader

A skill-grading skill for Claude Code. Evaluates a Claude Skill against a 12-dimension rubric and emits an actionable, severity-tagged report.

skill-grader answers *"is this skill any good, and what specifically is wrong with it?"* It is a judgment-and-reporting layer: it produces findings, it does not author or rewrite skills.

## Usage

```
skill-grader <path-to-skill>              # single skill, static mode
skill-grader <path> --empirical           # adds behavioural measurement (Claude Code only)
skill-grader <dir> --batch                # discovers */SKILL.md, grades each
skill-grader <path> --set-baseline        # grade and save result as baseline
skill-grader <path> --profile style       # override auto-detected profile
skill-grader <path> --emit-issues         # adds issues.json + issues.csv
skill-grader --self                       # grade this skill under the workflow profile
```

## Install

```bash
./install.sh
```

Copies the skill payload into `~/.claude/skills/skill-grader/` and stamps `.installed-from` with the source commit. Re-run after changes to update the live skill.

## Pipeline

| Step | Description | Script |
|------|-------------|--------|
| 1 | Mechanical scan — line counts, orphans, dangling refs, caps density | `scripts/scan.py` |
| 2 | Archetype detection — pick a weight profile from structure | `scripts/detect_profile.py` |
| 3 | Judgment scoring — Claude scores each dimension against the rubric | *(model, per `references/rubric.md`)* |
| 4 | Grade computation — weighted score, letter grade, baseline delta | `scripts/score.py` |
| 5 | Reporting — Markdown and self-contained HTML | `scripts/render.py` |
| 6 | Issue export — findings at major and above (optional) | `scripts/emit_issues.py` |

Everything mechanically checkable lives in `scan.py`, not in prose. The model's judgment is spent on the dimensions that genuinely require reading for meaning.

## Rubric

Twelve dimensions, each scored 0–4 against anchored descriptors in `references/rubric.md`.

| # | Dimension | Checks |
|---|-----------|--------|
| 1 | Description Triggering | What + when stated? Trigger phrases? Negative scope? |
| 2 | Trigger Surface Coverage | Realistic phrasings? Oblique? Sibling collisions? |
| 3 | Progressive Disclosure | SKILL.md within ~500 lines? Detail in `references/`? |
| 4 | Resource Hygiene | No orphans, no dangling refs, no duplication? |
| 5 | Script vs. Prose | Deterministic work scripted, not prose? |
| 6 | Instructional Voice | Imperative, rationale-over-mandate, low caps? |
| 7 | Output Contract | Format pinned to template or schema? |
| 8 | Examples | Present, generalising, not overfit? |
| 9 | Environment Portability | Assumptions declared? Degradation paths? |
| 10 | Least Surprise / Safety | Intent match? No surprise effects? **Gating.** |
| 11 | Script Correctness | Bundled scripts unit-tested? **N/A when no `scripts/`** |
| 12 | Behavioral Evals | Trigger and quality evals present? Assertions appropriate? |

Dimension 10 is gating: any blocker finding caps the overall grade regardless of weighted score.

D11 and D12 are deliberately separate. Unit tests catch a script that computes the wrong answer; evals catch a description that never fires or instructions that produce worse output than no skill at all. A skill can pass one completely while failing the other, so coverage of one never satisfies the other.

## Weight profiles

A flat weighting produces unfair grades across skill archetypes. Profiles live in `config/profiles.yaml`.

| Profile | Fits | Weighted up | N/A |
|---------|------|-------------|-----|
| `workflow` | Multi-step pipelines with scripts and artifacts | 4, 5, 7, 11, 12 | — |
| `style` | House-style and formatting rules | 6, 7, 8, 12 | 11 |
| `reference` | Domain knowledge, minimal procedure | 2, 3, 4, 12 | 5, 11 |
| `balanced` | Fallback when archetype is unclear | flat | — |

Marking a dimension N/A excludes it and renormalises the total rather than scoring it zero. The report always names the profile used and lists N/A dimensions — a grade is uninterpretable without knowing how it was weighted.

## Grading target: installed skill vs. codebase

An installed skill and its source repo are different objects and legitimately score differently. The installed copy carries neither tests nor evals; the repo carries those plus docs and plans. `scan.py` detects which it is looking at — via `.installed-from`, then `.git`, then location — and the report names it.

| Target | Answers | D11 / D12 | Overall grade |
|--------|---------|-----------|---------------|
| Installed skill | Is what's deployed current, complete and safe? | not assessable | **none — partial assessment** |
| Source codebase | Is this skill any good? | scored | letter grade |

An install payload is what the skill reads or executes while running, and nothing consults `tests/` or `evals/` at runtime. So an installed target cannot speak to verification at all.

It gets **no overall grade** as a result. Excluding two dimensions renormalises over the remaining ten, which would make a target that merely carries less evidence score *higher* than a complete one — code-audit graded A- installed against C+ for its own repo before this was fixed. There is no denominator that makes 10-of-12 comparable to 12-of-12, so the installed report gives per-dimension scores, findings, and provenance, and stops there.

Installed reports add a provenance line derived from `.installed-from`: whether the payload matches its source, how far it has drifted, and whether it was installed from a tree with uncommitted changes.

Grade both for the full picture. A path symlinked into the skills directory resolves to its real location and reads as a codebase.

## Output

| File | When | Purpose |
|------|------|---------|
| `grade.md` | Always | Default artifact — human-readable report |
| `grade.html` | Always | Self-contained report, no external assets |
| `grade.json` | Always | Machine-readable, for baselines and CI gating |
| `issues.json` | `--emit-issues` | Findings at major and above, shaped for `gh issue create` |
| `issues.csv` | `--emit-issues` | Same, for importer tooling |

Baselines are written to `.skill-grader/baseline.json` in the graded skill's directory. Subsequent runs report per-dimension deltas and flag regressions.

## Development

```bash
uv sync             # install dependencies
uv run pytest       # run the test suite
```

Fixtures in `tests/fixtures/` hold deliberately flawed skills, one per dimension, each with an expected score band. They exist to keep the rubric honest: a self-grade is only trustworthy if the fixture suite still discriminates.

## Layout

```
skill-grader/
├── SKILL.md                 # workflow, mode selection, rubric summary
├── install.sh               # copy payload into ~/.claude/skills/
├── issues.md                # issue log
├── references/
│   ├── rubric.md            # anchored 0–4 descriptors per dimension
│   ├── static-checks.md     # mechanical vs. judged
│   ├── empirical.md         # Mode B delegation to skill-creator
│   └── issue-import.md      # gh one-liner, labels, dedup
├── scripts/                 # scan, detect_profile, score, render, emit_issues,
│                            # sync_issues (issues.md <-> GitHub reconciliation)
├── assets/                  # report CSS and HTML templates
├── config/profiles.yaml     # weight profiles
├── evals/
│   ├── trigger_eval.json    # queries that should and should not trigger
│   └── evals.json           # task prompts with assertions
├── tests/fixtures/          # deliberately flawed skills, one per dimension
└── docs/spec.md             # design spec
```
