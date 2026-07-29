# Issues

Tracked on GitHub at [mig2/skill-grader](https://github.com/mig2/skill-grader/issues) and mirrored here.

## Closed

### #1 — Rubric descriptors and test fixtures for all 11 dimensions
- **Labels:** enhancement
- **Description:** The rubric and its fixtures co-design. Anchored 0–4 descriptors written in the abstract come out vague; written against a concretely flawed fixture they come out sharp. Write both together.
- **Spec:** `docs/spec.md` §3, §11 step 1
- **Resolution:** Added `references/rubric.md` with anchored descriptors for all eleven dimensions, a gold fixture scoring 3–4 throughout, and eleven flawed fixtures that each fail exactly one dimension.
- **Commit:** 9aba110
- **Closed:** 2026-07-28

### #2 — scan.py: mechanical checks
- **Labels:** enhancement
- **Description:** Everything mechanically checkable belongs in a script, not in prose. Line counting is not a job for model judgment.
- **Spec:** `docs/spec.md` §7, §11 step 2
- **Resolution:** Added `scripts/scan.py` covering line counts, orphaned files, dangling references, caps density, TOC presence, content duplication, and deterministic-prose signals. 16 tests.
- **Commit:** ded2041
- **Closed:** 2026-07-28

### #3 — Project scaffolding: uv, profiles, test setup
- **Labels:** setup
- **Description:** Initialise the project with uv, Python 3.13, PyYAML, Jinja2, and pytest. Add the weight-profile config and shared test fixtures.
- **Resolution:** Added `pyproject.toml`, `config/profiles.yaml` with four profiles, `tests/conftest.py`, and `.gitignore`. Removed the `uv init` stub.
- **Commits:** bf3318a, 0c28013
- **Closed:** 2026-07-28

### #4 — detect_profile.py: archetype heuristic
- **Labels:** enhancement
- **Description:** A flat weighting produces unfair grades across archetypes. Detect the archetype from structure — presence of `scripts/`, ratio of procedural to declarative content, whether outputs are artifacts — and pick a profile.
- **Spec:** `docs/spec.md` §3, §11 step 3
- **Resolution:** Added `scripts/detect_profile.py` returning profile, reasoning, and signals. 5 tests.
- **Commit:** e913c6f
- **Closed:** 2026-07-28

### #5 — score.py: weighted scoring and baseline delta
- **Labels:** enhancement
- **Description:** Weighted mean over applicable dimensions normalised to 0–100, mapped to a letter grade. N/A dimensions excluded and renormalised rather than scored zero. Baseline comparison for regression tracking.
- **Spec:** `docs/spec.md` §3, §4
- **Resolution:** Added `scripts/score.py` with `compute_score`, `to_letter_grade`, `compute_delta`, `build_grade_result`, and baseline load/save. 12 tests.
- **Commit:** d1b97dc
- **Closed:** 2026-07-28

### #6 — render.py: Markdown and HTML report generation
- **Labels:** enhancement
- **Description:** Emit a scorecard and findings as Markdown readable inline in a chat window, plus a self-contained HTML report with no external assets.
- **Spec:** `docs/spec.md` §5, §9
- **Resolution:** Added `scripts/render.py` with `render_markdown` and `render_html`, plus `assets/report.css.template` and `assets/report.html.template`. 9 tests.
- **Commit:** 434c02a
- **Closed:** 2026-07-28

### #7 — SKILL.md: skill workflow
- **Labels:** enhancement
- **Description:** The skill entry point: mode selection, invocation patterns, the grading workflow, a rubric summary, and the output contract. Largely a summary of the rubric, so easier to write once the rubric is real.
- **Spec:** `docs/spec.md` §11 step 4
- **Resolution:** Added `SKILL.md` at 133 lines, within the ~500 budget, with detail delegated to `references/`.
- **Commit:** 0e6edd0
- **Closed:** 2026-07-28

### #8 — emit_issues.py: GitHub issue export
- **Labels:** enhancement
- **Description:** Export findings at major and above, shaped for import into GitHub. Each body carries a stable fingerprint so re-runs do not produce duplicates. The skill emits the file; it does not file the issues.
- **Spec:** `docs/spec.md` §5
- **Resolution:** Added `scripts/emit_issues.py` producing `issues.json` and `issues.csv` with severity and dimension labels and a `<!-- sg:<hash> -->` fingerprint marker. 7 tests.
- **Commit:** 9079ca3
- **Closed:** 2026-07-28

### #9 — Bug: render.py JSON round-trip key handling and skill name resolution
- **Labels:** bug
- **Description:** Found during the first live grading runs. Three defects: `render.py` read `grade_result["scan"]` while `score.py` writes `scan_result`; dimension keys become strings after a JSON round-trip but were looked up as ints, rendering every score as `None`; and `Path(".").name` returns an empty string, titling reports "Unknown Skill".
- **Resolution:** Added a `_get_flex` helper tolerating either key type, accepted both scan key names, and resolved paths before taking `.name`.
- **Commits:** 8ab4739, 41c0c73
- **Closed:** 2026-07-28

### #10 — Reference documents: static-checks, empirical, issue-import
- **Labels:** documentation
- **Description:** Supporting references for the workflow: which dimensions are mechanically checkable versus judged, how empirical mode delegates to skill-creator, and how to import emitted issues.
- **Spec:** `docs/spec.md` §7
- **Resolution:** Added `references/static-checks.md`, `references/empirical.md`, and `references/issue-import.md`.
- **Commit:** f497bfe
- **Closed:** 2026-07-28

### #11 — Dimension names do not match the spec
- **Labels:** bug
- **Description:** `DIMENSION_NAMES` in `score.py` shipped with invented names ("scope clarity", "error handling", "metadata quality") that do not match the eleven dimensions in `docs/spec.md`. Reports rendered the wrong labels.
- **Resolution:** Corrected to the spec names.
- **Commit:** 7dd467c
- **Closed:** 2026-07-28

### #12 — Move spec to canonical docs/spec.md
- **Labels:** documentation
- **Description:** The spec landed as `docs/skill-grader-spec.md`, but its own repo-conventions section specifies `docs/spec.md`.
- **Resolution:** Renamed so the spec matches the convention it defines.
- **Commit:** 1fc78d7
- **Closed:** 2026-07-28

### #17 — Gitignore generated grade outputs
- **Labels:** cleanup
- **Description:** Grading runs write `grade.md`, `grade.html`, `grade.json`, and per-target variants into the repo root. These are generated artifacts and should not be tracked.
- **Resolution:** Added them to `.gitignore`. `scan.py` also consults `git check-ignore` in codebase mode, so generated files are not counted as orphans.
- **Commits:** 480c557, 0678816
- **Closed:** 2026-07-29

### #19 — First live grading runs
- **Labels:** testing
- **Description:** Spec build order step 6: run the grader against real skills and record the results.
- **Spec:** `docs/spec.md` §11 step 6
- **Resolution:** Graded three targets — skill-grader itself (codebase, B 86.5), the installed code-audit (installed, C+ 78.8), and the skill-audit repo (codebase, B+ 87.5). The runs surfaced #9, #13, and #14.
- **Commits:** 8ab4739, 41c0c73, 0678816, 6cbf8a9
- **Closed:** 2026-07-29

### #13 — Grading an installed skill and grading its codebase are different jobs
- **Labels:** enhancement
- **Description:** The same skill scored C+ (78.8) as an installed copy and B+ (87.5) as a source repo — nine points apart, because the installed copy ships no tests and the repo carries docs and plans. Both grades are correct; they describe different objects. The problem was that the grader did this silently, making the score uninterpretable.
- **Resolution:** `scan.py` detects mode from `.installed-from`, then `.git`, then location, and reports it. Paths resolve first so a symlinked repo reads as a codebase. Codebase mode excludes repo furniture and gitignored output from orphan detection. Reports carry a header note naming the mode and pointing at the other half of the picture. D11 still scores 0 on an installed skill rather than N/A, so the testability gap prompts action instead of hiding.
- **Commit:** 0678816
- **Closed:** 2026-07-29

### #14 — Resource hygiene false positives: script-referenced files and package markers
- **Labels:** bug
- **Description:** Reference scanning read prose but not scripts, so a template loaded by `render.py` was flagged orphaned despite being used. `__init__.py` was flagged too, though package markers exist for the interpreter rather than to be linked from prose. Affected real targets: code-audit's asset templates are loaded by `render_report.py` and were reported as findings during grading.
- **Resolution:** Scripts are now scanned as reference sources, and package markers are never counted. code-audit orphans 7 → 5, skill-grader 4 → 0.
- **Commit:** 6cbf8a9
- **Closed:** 2026-07-29

### #15 — Add README
- **Labels:** documentation
- **Description:** The repo has no README.
- **Resolution:** Added `README.md` covering usage, install, the pipeline, the rubric, weight profiles, the installed-versus-codebase distinction, outputs, and layout. Linked from SKILL.md and shipped in the install payload.
- **Commit:** c6d77dc
- **Closed:** 2026-07-29

### #18 — Add install script with git hash stamp
- **Labels:** setup, tooling
- **Description:** The skill was deployed by symlinking the whole repo into `~/.claude/skills/`, exposing `tests/`, `docs/`, `.venv/`, and generated reports as part of the skill.
- **Resolution:** Added `install.sh` copying SKILL.md, README.md, `scripts/`, `references/`, `assets/`, `config/`, and the project manifest, stamping `.installed-from` with the short hash. The stamp doubles as the signal `scan.py` uses to detect an installed skill.
- **Commit:** c6d77dc
- **Closed:** 2026-07-29

### #16 — Add issues.md log
- **Labels:** documentation
- **Description:** Work was tracked on GitHub but not in-tree.
- **Resolution:** Added this file, mirroring code-audit's convention: one entry per issue with labels, description, resolution, commit hash, and close date.
- **Closed:** 2026-07-29

## Open

None.

## Known limitations

Not yet filed as issues, but recorded during live grading runs:

- **Dynamically referenced files read as orphans.** code-audit's `SKILL.md` instructs the reader to open `references/lang/<x>.md` for each detected language. `scan.py` matches literal paths, so the five files never named literally (`go`, `java`, `python`, `rust`, `swift`) are reported as orphaned. This is the sole remaining D4 finding on code-audit and is a scanner limitation rather than a defect in that skill.
- **No end-to-end integration test.** Unit tests cover each script, but nothing runs the full pipeline (scan → detect → score → render) against a fixture and asserts the resulting grade. Raised by skill-grader's own self-grade as a D11 nit.
