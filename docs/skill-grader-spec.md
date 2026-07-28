# skill-grader — Specification

**Status:** draft v0.1 — for review, not yet implemented
**Scope decisions:** static grading is the default path, empirical grading is opt-in; emits Markdown + HTML; single-skill by default, batch supported.

---

## 1. Purpose

Grade the quality of a Claude Skill and emit an actionable, severity-tagged report.

skill-grader answers *"is this skill any good, and what specifically is wrong with it?"* It is a judgment-and-reporting layer. It deliberately does **not** reimplement authoring or eval-running — where empirical measurement is needed it calls out to `skill-creator`'s existing harness.

### Non-goals

- Verifying domain correctness of a skill's subject matter. It cannot tell you whether a Mishnah house-style rule is *right*, only whether it is stated unambiguously.
- General-purpose security scanning of bundled code. It flags surface and intent mismatches, not CVEs.
- Authoring or rewriting skills. It produces findings; acting on them is a separate step.

---

## 2. Modes

### Mode A — Static (default)

Reads `SKILL.md` plus all bundled resources. No execution, no model calls beyond the grading pass itself. Runs anywhere: Claude.ai, Cowork, Claude Code.

### Mode B — Empirical (opt-in, `--empirical`)

Measures actual behaviour: trigger rate against generated queries, and with-skill vs. baseline output quality. Requires subagents and the `claude` CLI, so it is Claude Code only.

Mode B **delegates** rather than duplicates:

| Need | Delegate to |
|---|---|
| Trigger-rate measurement | `skill-creator/scripts/run_eval.py` |
| With-skill vs. baseline runs | skill-creator subagent workflow |
| Benchmark aggregation | `skill-creator/scripts/aggregate_benchmark.py` |

skill-grader's contribution in Mode B is *interpretation*: folding measured trigger rate and output lift back into the rubric as scored dimensions, and reconciling them against the static findings. A skill can score well statically and still under-trigger; that contradiction is itself a headline finding.

If Mode B is requested in an environment that cannot support it, degrade to Mode A and say so explicitly in the report rather than silently skipping.

---

## 3. Rubric

Eleven dimensions. Each scored **0–4** against anchored descriptors, with configurable weights.

| # | Dimension | What it checks |
|---|---|---|
| 1 | **Description triggering** | Does the description state both *what* and *when*? Concrete trigger phrases and contexts, not just capability. Appropriately assertive — under-triggering is the known failure mode. Negative scope ("do NOT use for…") stated where the boundary is contestable. |
| 2 | **Trigger surface coverage** | Do the stated contexts cover realistic user phrasings, including oblique ones? Collisions with sibling skills that would make routing ambiguous. |
| 3 | **Progressive disclosure** | SKILL.md line count against the ~500 budget. Is detail correctly pushed into `references/`? Do reference files over ~300 lines carry a table of contents? |
| 4 | **Resource hygiene** | Orphaned files present but never referenced. Dangling pointers referenced but missing. Content duplicated between SKILL.md and a reference file. |
| 5 | **Script vs. prose allocation** | Deterministic or repetitive work written as prose steps the model must re-derive each run, where a script would be faster and stable. |
| 6 | **Instructional voice** | Imperative form. Rationale-over-mandate ratio — explaining *why* outperforms stacked MUSTs. Density of ALL-CAPS imperatives treated as a smell, not a virtue. |
| 7 | **Output contract** | If the skill produces artifacts, is the format pinned to an exact template? Loose output contracts are a leading cause of run-to-run inconsistency. |
| 8 | **Examples** | Presence, and whether they generalise. Examples narrow enough to be overfit are worse than none — they anchor the model to a single case. |
| 9 | **Environment portability** | Undeclared assumptions about subagents, browser, display, or CLI availability. Does it degrade gracefully, and does it *say* how? |
| 10 | **Least surprise / safety** | Contents match stated intent. No unexpected network egress, filesystem writes outside declared paths, or instruction-injection surface in bundled files. Any finding here is an automatic blocker regardless of score. |
| 11 | **Testability** | Does the skill ship evals? Are assertions objective where the output is objective — and correctly *absent* where the output is subjective? |

### Scoring

- Overall = weighted mean over *applicable* dimensions, normalised to 0–100, mapped to a letter grade.
- Dimension 10 is gating: any blocker finding caps the overall grade regardless of weighted score.

### Weight profiles

The eleven dimensions do not matter equally across skill archetypes, and a flat weighting produces unfair grades. A profile is a named weight vector plus a set of dimensions marked **N/A**.

| Profile | Fits | Weighted up | N/A |
|---|---|---|---|
| `workflow` | Multi-step pipelines with scripts and artifacts | 4, 5, 7, 11 | — |
| `style` | House-style and formatting rules | 6, 7, 8 | 11 (output is judged, not asserted) |
| `reference` | Domain knowledge, minimal procedure | 2, 3, 4 | 5, 11 |
| `balanced` | Fallback when archetype is unclear | flat | — |

Marking a dimension N/A **excludes it and renormalises the total**. It is not scored zero. A style skill correctly has no objective assertions; penalising it for their absence would reward a design error.

Profiles live in `config/profiles.yaml`. The grader auto-detects an archetype from structure — presence of `scripts/`, ratio of procedural to declarative content, whether outputs are artifacts or transformed text — and states its guess. `--profile <name>` overrides. **The report always names the profile used and lists N/A dimensions**, because a grade is uninterpretable without knowing how it was weighted.

### Findings

Every finding carries: dimension, severity (`blocker` / `major` / `minor` / `nit`), location (`file:line` where determinable), a one-line statement of the problem, and a concrete suggested fix. Findings are the useful output; the score is the summary.

---

## 4. Baselining

Grades are stored so quality can be tracked over time.

- Each run writes `.skill-grader/baseline.json` in the graded skill's directory.
- Subsequent runs report per-dimension deltas and flag regressions.
- `--set-baseline` accepts the current state as the new reference.
- Absent a baseline, the run is marked *initial* and no deltas are reported.

---

## 5. Outputs

### `grade.md`
Scorecard table, then findings grouped by severity. Readable inline in a chat window — no rendering step required. This is the default artifact.

### `grade.html`
Self-contained, no external assets. Publication-quality with a deliberate typographic identity. Single-skill view: score header, dimension breakdown with anchored descriptors visible on hover, findings list with source excerpts. Batch view: dashboard with a sortable skill × dimension matrix, heat-mapped, plus per-skill drill-down.

### `grade.json` (internal)
Not a headline deliverable, but produced regardless — baselining, delta computation, and batch aggregation all need machine-readable output. Available if wanted for CI gating later.

### `issues.json` / `issues.csv` (optional, `--emit-issues`)
Findings at `major` and above, shaped for import into GitHub. JSON is an array of `{title, body, labels}` for `gh issue create` scripting; CSV suits importer tooling.

- **Title:** `[skill-grader] <skill>: D<n> <dimension> — <short problem>`
- **Labels:** severity + dimension slug, e.g. `severity:major`, `dim:progressive-disclosure`
- **Body:** problem statement, location, suggested fix, and the rubric anchor that was missed

**skill-grader emits the file; it does not file the issues.** Creating issues is side-effectful and belongs to an explicit step the user runs — a `gh` one-liner is shipped in `references/issue-import.md`.

Each issue body carries a stable fingerprint marker (`<!-- sg:<hash> -->`) derived from skill, dimension, location, and normalised problem text. Re-runs match against existing open issues by fingerprint so a weekly grade does not produce weekly duplicates. Findings that no longer reproduce are reported as *resolved* in the delta section rather than auto-closed.

---

## 6. Invocation

```
skill-grader <path-to-skill>              # single, static, default
skill-grader <path> --empirical           # adds Mode B (Claude Code only)
skill-grader <dir> --batch                # discovers */SKILL.md beneath dir
skill-grader <path> --set-baseline
skill-grader <path> --profile style      # override archetype auto-detection
skill-grader <path> --emit-issues        # adds issues.json + issues.csv
skill-grader --self                      # grade skill-grader against itself
```

Batch mode discovers every `SKILL.md` under the target, grades each independently, then emits per-skill `grade.md` files plus one dashboard `grade.html`. Batch is always static-only in the first version — empirical batch grading is expensive enough to deserve an explicit decision later.

---

## 7. Layout

```
skill-grader/
├── SKILL.md                    # workflow, mode selection, rubric summary
├── references/
│   ├── rubric.md               # anchored 0–4 descriptors per dimension
│   ├── static-checks.md        # what is mechanically checkable vs. judged
│   ├── empirical.md            # Mode B delegation to skill-creator
│   └── issue-import.md         # gh one-liner, label setup, dedup behaviour
├── scripts/
│   ├── scan.py                 # mechanical checks: line counts, orphans,
│   │                           # dangling refs, caps density, TOC presence
│   ├── detect_profile.py       # archetype heuristic → profile guess
│   ├── score.py                # weights → score → grade, baseline delta
│   ├── render.py               # grade.json → grade.md + grade.html
│   └── emit_issues.py          # grade.json → issues.json + issues.csv
├── assets/
│   └── report.css.template     # inlined by render.py
├── tests/
│   └── fixtures/               # deliberately flawed skills, one per dimension
└── config/
    └── profiles.yaml
```

Design note: everything mechanically checkable belongs in `scan.py`, not in prose. The model's judgment should be spent on dimensions 1, 2, 5, 6, 7, and 8 — the ones that genuinely require reading for meaning. Line counting is not one of them.

---

## 8. Self-grading

`--self` grades skill-grader against its own rubric. This is a required test, not a curiosity: a grading skill that scores poorly on its own criteria is either wrong about the criteria or wrong about itself, and both are worth knowing.

Two guards against the obvious failure mode — a grader that flatters itself:

1. **Fixture suite.** `tests/fixtures/` holds deliberately flawed skills, one per dimension, each with an expected score band. A self-grade is only trusted if the fixture suite still discriminates. This catches rubric drift toward whatever skill-grader happens to do.
2. **Declared profile.** skill-grader self-grades under `workflow`, fixed, not auto-detected. Letting it choose its own weighting is exactly the loophole to close.

Self-grade output is committed alongside the skill so its score history is visible in the same way it makes everyone else's visible.

---

## 9. Visual identity

`grade.html` inherits `code-audit`'s dashboard idiom — shared type scale, palette, severity colour coding, and card/matrix layout — so the two read as one toolchain.

**Blocker:** `code-audit` is not visible from this environment; only `mishnah` is mounted under the user skills directory. To match rather than approximate, I need either the report template or a rendered sample HTML from a `code-audit` run. Until then this section is intent, not specification.

---

## 10. Remaining open questions

1. **Fixture provenance.** Hand-write the flawed fixtures, or derive them by mutating real skills? Mutation gives more realistic failures; hand-written gives cleaner one-dimension isolation.
## 11. Build order

1. **`references/rubric.md` and `tests/fixtures/` together.** These co-design. Anchored 0–4 descriptors written in the abstract come out vague; written against a concretely flawed fixture they come out sharp. Resolve fixture provenance (§10.1) here, since it determines what everything downstream is tested against.
2. **`scan.py`.** Mechanical checks only, no model judgment, unit-testable against the fixtures. Stays correct as the rubric evolves.
3. **`detect_profile.py`.** Calibrate the archetype heuristic against real skills — `mishnah` and `code-audit` sit at opposite ends and make a reasonable two-point check.
4. **`SKILL.md`.** Largely a summary of the rubric plus mode selection, so it is far easier to write once the rubric is real.
5. **`score.py`, then `render.py`, then `emit_issues.py`.** Resolve §9 against the actual `code-audit` template before writing `render.py`.
6. **First live runs.** `--self`, then `mishnah` and `code-audit`.

### Repo conventions

- Keep this spec in-tree as `docs/spec.md` and update it as decisions land. A spec that drifts from the build stops being useful as the thing you check against.
- Git from the first commit: baselines and self-grade history are specified to be committed, and retrofitting that loses the history that makes them worth having.

