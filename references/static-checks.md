# Static Checks Reference

Which dimensions are mechanically checkable vs. judgment-required.

## Mechanically Checked (scan.py output)

These dimensions have quantitative measurements from scan.py. Use the scan result as a scoring floor.

| Dimension | Scan Key | What It Measures |
|-----------|----------|-----------------|
| D3: Progressive Disclosure | `skill_md_lines` | SKILL.md line count against ~500 budget |
| D4: Resource Hygiene | `orphaned_files`, `dangling_refs`, `duplicated_blocks` | Orphaned files, dangling references, content duplication |
| D5: Script vs. Prose | `deterministic_prose_signals`, `has_scripts` | Prose describing deterministic work; presence of scripts/ |
| D6: Instructional Voice | `caps_density`, `caps_lines` | ALL-CAPS imperative density (>5% is a smell) |
| D11: Script Correctness | `has_unit_tests`, `has_scripts` | Recognisable test files in `tests/` or `test/`. **N/A when `has_scripts` is false** |
| D12: Behavioral Evals | `has_trigger_evals`, `has_quality_evals`, `has_eval_assertions`, `eval_files` | Eval files under `evals/`, classified by type, and whether assertions are non-empty |

## Judgment-Required (model evaluation)

These dimensions cannot be measured mechanically — they require reading the skill for meaning.

| Dimension | What to Evaluate |
|-----------|-----------------|
| D1: Description Triggering | Does the description state what AND when? Concrete trigger phrases? Negative scope? Assertiveness level? |
| D2: Trigger Surface Coverage | Do stated contexts cover realistic user phrasings including oblique ones? Sibling skill collisions? |
| D7: Output Contract | Is the output format pinned to an exact template/schema? All fields specified? |
| D8: Examples | Do examples generalise? Cover different cases? Or overfit to one narrow case? |
| D9: Environment Portability | Undeclared assumptions about subagents/browser/CLI? Graceful degradation? |
| D10: Least Surprise / Safety | Intent match? Unexpected network egress or filesystem writes? Injection surface? |

## Mixed Dimensions

Some dimensions get a measurement floor from scan.py and a judgment ceiling from model review:

- **D3**: scan.py gives the line count → if >500, floor is score 0-1. Model evaluates whether content is correctly pushed to references/.
- **D4**: scan.py finds orphans/dangling/duplication → structural floor. Model evaluates whether duplication is meaningful.
- **D5**: scan.py flags deterministic prose patterns → if many, floor is score 0-2. Model evaluates whether the flagged prose genuinely should be a script.
- **D6**: scan.py gives caps density → if >5%, floor is score 0-2. Model evaluates rationale quality and voice consistency.
- **D11**: scan.py reports whether test files exist → if absent while `has_scripts` is true, the score is 0. Presence only proves tests exist; the model judges whether they cover the scripts' real logic or only happy paths.
- **D12**: scan.py reports which eval types are present and whether assertions are non-empty → sets the floor. The model judges whether the trigger queries cover realistic phrasings, whether negative cases are genuinely tempting, and whether assertions are objective where the output is objective and correctly absent where it is subjective.

### Distinguishing D11 from D12

Both ask "can you tell if this works?", but about different things. Unit tests catch a script that computes the wrong answer. Evals catch a description that never fires, or instructions that produce worse output than no skill at all. A skill can pass one completely while failing the other, so never let coverage of one satisfy the other.

## Using Scan Results in Scoring

1. Run scan.py and read the output
2. For each mechanically-checked dimension, assign a floor score based on the scan values
3. For each judgment dimension, read the skill and score against the rubric
4. For mixed dimensions, start from the scan floor and adjust based on judgment
5. Compile all 11 scores for score.py
