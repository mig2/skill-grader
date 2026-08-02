# Skill Grader Rubric

Anchored 0–4 descriptors for all 12 dimensions. Each score is defined by concrete, observable criteria so that two independent graders reach the same score on the same fixture.

---

## Dimension 1: Description Triggering

Does the SKILL.md description tell an LLM *when* to invoke the skill, *what* it does, and *when not* to?

| Score | Descriptor |
|-------|------------|
| 0 | Description missing or states only capability with no trigger context (e.g., "Helps with code") |
| 1 | Mentions context but vague; no concrete trigger phrases; negative scope absent |
| 2 | States what/when but uses generic trigger phrases; negative scope absent or absent |
| 3 | Clear what/when, concrete triggers, negative scope present, but slightly under-assertive or missing one edge |
| 4 | Precise what/when, concrete triggers covering direct and oblique phrasings, negative scope clearly stated, appropriately assertive |

---

## Dimension 2: Trigger Surface Coverage

Does the skill trigger on the realistic range of ways a user might express the need?

| Score | Descriptor |
|-------|------------|
| 0 | No trigger phrases or contexts stated anywhere in the skill |
| 1 | One or two literal trigger phrases only; would miss most realistic phrasings or oblique requests |
| 2 | Covers direct phrasings but misses oblique; no mention of sibling skill collision |
| 3 | Direct and some oblique phrasings covered; sibling collisions acknowledged |
| 4 | Comprehensive coverage of direct, oblique, and edge-case phrasings; sibling boundaries explicitly drawn |

---

## Dimension 3: Progressive Disclosure

Is complexity pushed out of SKILL.md into references/, keeping the main file scannable?

| Score | Descriptor |
|-------|------------|
| 0 | SKILL.md exceeds 800 lines with no references/ directory |
| 1 | SKILL.md exceeds 500 lines; content could be pushed to references/ |
| 2 | Within line budget but large reference files lack a table of contents |
| 3 | Within line budget, references used appropriately, large refs have TOCs, minor issues |
| 4 | Concise and focused SKILL.md; all heavy detail in references/; every large ref has a TOC |

---

## Dimension 4: Resource Hygiene

Are all referenced files present and all present files referenced?

| Score | Descriptor |
|-------|------------|
| 0 | Multiple orphaned files and/or dangling references; significant content duplication |
| 1 | At least one orphaned file or dangling reference present; some duplication |
| 2 | No orphans or dangling refs but non-trivial content duplication exists |
| 3 | Clean reference graph, minimal duplication, only minor issues |
| 4 | Every file referenced and exists, zero duplication, perfectly clean resource graph |

---

## Dimension 5: Script vs Prose Allocation

Is deterministic, mechanical work scripted rather than described as prose steps?

| Score | Descriptor |
|-------|------------|
| 0 | All deterministic work described entirely as prose steps with no scripts |
| 1 | Most deterministic work is prose; only a few scripts or none present |
| 2 | Mix of scripts and prose; some clearly deterministic work remains as manual steps |
| 3 | Most deterministic work is scripted; prose reserved for judgment; minor gaps |
| 4 | All deterministic work scripted; prose only for judgment calls; scripts expose --help |

---

## Dimension 6: Instructional Voice

Are instructions direct, imperative, and free of unnecessary emphasis?

| Score | Descriptor |
|-------|------------|
| 0 | Passive or ambiguous voice throughout; descriptions rather than directives |
| 1 | Mix of imperative and passive voice; heavy ALL-CAPS usage (>5% of instruction lines); no rationale for mandates |
| 2 | Mostly imperative; some caps density; partial rationale for key mandates |
| 3 | Consistent imperative voice; rationale-over-mandate pattern followed; low caps usage |
| 4 | Clean imperative throughout; every non-obvious mandate accompanied by rationale; caps used sparingly and deliberately |

---

## Dimension 7: Output Contract

Is the format of every artifact the skill produces precisely specified?

| Score | Descriptor |
|-------|------------|
| 0 | Skill produces artifacts but format is not specified at all |
| 1 | Format mentioned by name but not pinned to a template or schema |
| 2 | Partially specified; some fields or ordering left ambiguous |
| 3 | Pinned to a template or schema; only minor ambiguities remain |
| 4 | Exact template or schema provided; all fields, ordering, and formatting specified |

---

## Dimension 8: Examples

Do the examples generalise across realistic input variation?

| Score | Descriptor |
|-------|------------|
| 0 | No examples present |
| 1 | Examples overfit to a single narrow case; would anchor the model to one context |
| 2 | One case covered well but the examples do not generalise to other realistic inputs |
| 3 | Multiple examples covering different cases; minor gaps in coverage |
| 4 | Examples generalise across input types, edge cases, and varied contexts |

---

## Dimension 9: Environment Portability

Does the skill declare its environmental assumptions and degrade gracefully when they are unmet?

| Score | Descriptor |
|-------|------------|
| 0 | Assumes a specific environment with no acknowledgment; would silently fail in other contexts |
| 1 | Assumptions partially documented; no degradation paths stated |
| 2 | Assumptions documented but degradation described only vaguely |
| 3 | Assumptions documented with specific degradation paths; minor gaps |
| 4 | All assumptions declared; graceful degradation with an explicit fallback for each dependency |

---

## Dimension 10: Least Surprise / Safety

Do the skill's instructions match its stated intent, with no unexpected side effects?

| Score | Descriptor |
|-------|------------|
| 0 | Contents do not match stated intent; unexpected egress, writes, or injection risk present. **Automatic blocker — do not deploy.** |
| 1 | Intent mostly matches but undeclared side effects present |
| 2 | No undeclared side effects but injection surface exists |
| 3 | Clean safety posture with only minor concerns |
| 4 | Exactly matches stated intent; no unexpected effects; no injection surface; only declared file paths and network calls |

---

## Dimension 11: Script Correctness

Are the scripts the skill bundles verified by unit tests?

**N/A when the skill ships no `scripts/`.** A prose-only skill has nothing to unit test; that is a correct design, not a gap.

This dimension is about the deterministic code, not the skill's behaviour — a skill whose `scan.py` miscounts lines is broken however well it triggers. Behaviour is Dimension 12.

| Score | Descriptor |
|-------|------------|
| 0 | Scripts are present with no tests of any kind |
| 1 | A token test or two; most scripts and most logic untested |
| 2 | Some scripts tested, but significant gaps — core logic paths uncovered |
| 3 | Most scripts tested with real assertions; minor gaps or happy-path bias |
| 4 | All scripts tested including edge cases and failure modes; tests verify behaviour rather than mocks |

---

## Dimension 12: Behavioral Evals

Does the skill ship evals that test *the skill itself* — whether it triggers, and whether its output is any good?

**Never N/A.** Every skill has a description that must fire on the right requests and stay quiet on the wrong ones, and output someone must be able to judge.

Two eval types, answering different questions:

- **Trigger evals** (`evals/trigger_eval.json`) — an array of `{query, should_trigger}` pairs. The negative cases matter as much as the positive ones: they catch a description that fires on everything.
- **Quality evals** (`evals/evals.json`) — task prompts with `expected_output` and `assertions`, proving the skill actually improves the result.

| Score | Descriptor |
|-------|------------|
| 0 | No evals of any kind; no way to tell whether the skill triggers or helps |
| 1 | Informal testing notes or example prompts in prose, but no structured eval files |
| 2 | Structured eval prompts exist, but assertions are missing, empty, or happy-path only |
| 3 | Trigger **or** quality evals with real assertions; the other type absent or thin |
| 4 | Both trigger and quality evals; negative trigger cases present; assertions objective where the output is objective and correctly **absent** where it is subjective |

Do not force assertions onto subjective outputs. A skill that produces prose or design should be evaluated qualitatively; inventing brittle string-match assertions for it scores worse, not better.
