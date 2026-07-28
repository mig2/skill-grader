---
name: code-reviewer
version: 1.0.0
author: example-team
tags: [code-review, quality]
---

# Code Reviewer

## Description

Review code changes and produce a report with your findings. Use this skill when the user asks for a code review, wants feedback on their code, or needs a quality assessment of a pull request. Trigger on phrasings like "review this code", "give me feedback on this PR", "what do you think of this code", or "code review please". Do not trigger on requests to explain code or write new code.

## When to Use

**Trigger conditions:**
- "Review this code"
- "Give me feedback on this PR"
- "Code review, please"
- "What do you think of this implementation?"
- "Can you check this before I merge?"

**Do not trigger when:**
- The user asks to explain code (use code-explainer skill)
- The user asks to write or modify code (use code-writer skill)
- The user asks for a security-specific review (use security-auditor skill)

## Instructions

1. Read all files provided. If a diff is provided, read the full diff. If whole files are provided, read the whole files.

2. Assess code quality across these dimensions:
   - Correctness: does the code do what it claims?
   - Readability: is the code easy to understand?
   - Maintainability: is the code structured to be easy to change?
   - Performance: are there obvious inefficiencies?
   - Security: are there obvious vulnerabilities?
   - Test coverage: are there tests, and are they adequate?

3. Identify all issues. Classify each issue by severity:
   - Blocker: must be fixed before merging
   - Major: should be fixed but not necessarily a hard blocker
   - Minor: nice to have, at reviewer's discretion
   - Nit: purely stylistic

4. For each issue, provide: the file and line reference, a description of the issue, and a suggested fix or approach.

5. Produce a report with your findings.

6. End with an overall recommendation: Approve, Request Changes, or Comment Only.

## Examples

**Example 1 — small function with a bug:**

Input: A 30-line Python function with an off-by-one error.

Expected output: Report identifies the off-by-one error as a Blocker with the specific line reference and a corrected version. Overall recommendation is Request Changes.

**Example 2 — well-written code:**

Input: A clean TypeScript module with good test coverage.

Expected output: Report finds only one Minor issue (a variable name that could be clearer). Overall recommendation is Approve.

**Example 3 — large PR:**

Input: A 500-line diff across multiple files.

Expected output: Report organised by file. Each file section lists its issues. Summary at the top shows total issue counts by severity.

## Environment and Portability

No external tools required. Operates on code provided in context.

## References

No bundled files.
