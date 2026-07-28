---
name: linter-runner
version: 1.0.0
author: example-team
tags: [linting, code-quality]
---

# Linter Runner

## Description

Run the project linter and report issues. Use this skill when the user says exactly "run the linter". This skill handles linting tasks.

## When to Use

**Trigger conditions:**
- "run the linter"

## Instructions

1. Identify the project root by looking for a `pyproject.toml`, `package.json`, or `.eslintrc` file.

2. Determine the appropriate linter based on the project type:
   - Python: use `ruff` if configured, otherwise `flake8`.
   - JavaScript/TypeScript: use `eslint`.
   - Other: check for a `lint` script in `package.json` or `Makefile`.

3. Run the linter on the full project, not just the changed files, unless the user specifies otherwise.

4. Collect the output and parse it into a structured list of issues.

5. Group issues by severity: errors first, then warnings, then informational.

6. Report the grouped issues using the output contract below.

7. If the linter exits with a non-zero code, report this explicitly.

8. If no issues are found, report a clean result.

## Output Contract

Produce a Markdown report in this format:

```markdown
# Linter Report

**Linter:** <tool name and version>
**Files checked:** <count>
**Total issues:** <count>

## Errors (<count>)

| File | Line | Rule | Message |
|------|------|------|---------|
| ... | ... | ... | ... |

## Warnings (<count>)

| File | Line | Rule | Message |
|------|------|------|---------|
| ... | ... | ... | ... |

## Summary

<One sentence describing the overall state.>
```

## Examples

**Example 1 — Python project with errors:**

Input: User says "run the linter" in a Python project with `ruff` configured.

Expected output: Linter report showing ruff errors grouped by severity, with file paths relative to the project root.

**Example 2 — Clean project:**

Input: User says "run the linter" in a project with no lint errors.

Expected output: Linter report showing 0 errors, 0 warnings, and a summary of "No issues found."

## Environment and Portability

Requires the relevant linter to be installed and on `PATH`. If the linter is not available, report which tool is missing and how to install it.

## References

No bundled files.
