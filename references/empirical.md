# Empirical Grading (Mode B)

Mode B adds measured behavioral data to the static grade. It is opt-in (`--empirical`) and requires Claude Code with subagent support.

## What It Measures

1. **Trigger rate** — does the skill actually trigger when it should?
   - Generates a set of test queries (direct, oblique, edge-case)
   - Measures what fraction correctly invoke the skill
   - A statically well-described skill that under-triggers is a headline finding

2. **Output quality lift** — does the skill improve output vs. baseline?
   - Runs the same queries with and without the skill
   - Compares output quality on the skill's own criteria
   - A skill that triggers but doesn't improve output has a different problem

## Delegation

Mode B delegates rather than duplicates:

| Need | Delegate To |
|------|------------|
| Trigger-rate measurement | `skill-creator/scripts/run_eval.py` |
| With-skill vs. baseline runs | skill-creator subagent workflow |
| Benchmark aggregation | `skill-creator/scripts/aggregate_benchmark.py` |

skill-grader's contribution is *interpretation*: folding measured trigger rate and output lift into the rubric as additional scored evidence, and reconciling against static findings.

## How Empirical Results Affect Scoring

- **D1 (Description Triggering)**: If trigger rate < 50%, cap D1 at 2 regardless of static assessment
- **D2 (Trigger Surface Coverage)**: Trigger rate by query type (direct vs. oblique) directly informs D2 score
- **D8 (Examples)**: If output quality lift is negligible, examples may be misleading — flag this

## Environment Requirements

- Claude Code with subagent support
- `claude` CLI available on PATH
- skill-creator accessible (check for `skill-creator/scripts/run_eval.py`)

## Graceful Degradation

If Mode B is requested in an environment that cannot support it:
1. Check for `claude` CLI availability
2. Check for skill-creator scripts
3. If either is missing: degrade to Mode A
4. Print explicit message: "Empirical grading requires Claude Code with subagent support. Falling back to static grading."
5. Include in report header: "Mode: Static (empirical requested but unavailable)"
