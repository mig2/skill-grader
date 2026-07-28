---
name: repo-health-checker
version: 1.0.0
author: example-team
tags: [repository, health, audit]
---

# Repository Health Checker

## Description

Audit a repository for common health indicators and produce a report. Use this skill when the user asks to check the health of a repository, audit a codebase for hygiene issues, or produce a repository quality report. Trigger on phrasings like "check the repo health", "audit this repository", "what's the state of this codebase", or "give me a health report". Do not trigger on requests to fix issues or refactor code.

## When to Use

**Trigger conditions:**
- "Check the repo health"
- "Audit this repository"
- "What's the state of this codebase?"
- "Give me a health report on this project"
- "Are there any hygiene issues in this repo?"

**Do not trigger when:**
- The user asks to fix identified issues
- The user asks to refactor or clean up code
- The user is asking about a single file rather than the whole repository

## Instructions

1. Count the lines in each source file in the repository. If any file has more than 500 lines, flag it as oversized. Do this for every file — do not skip any.

2. Scan the directory tree for all Markdown files. Check if each Markdown file has a top-level heading on the first line. If any file does not have a heading, flag it.

3. Check if the file `.gitignore` exists in the repository root. If it does not exist, flag the repository as missing a gitignore.

4. Count the number of TODO and FIXME comments across all source files. Report the total count and list the top five files by TODO density.

5. Scan the directory for all Python files. For each Python file, check if the file has a module-level docstring. Count the files that are missing docstrings.

6. Check if a `README.md` or `README.rst` file exists in the repository root. If it does not exist, flag the repository.

7. Check if a `LICENSE` file exists in the repository root. If it does not exist, flag the repository.

8. Count the total number of files in the repository, excluding `.git` contents. Report the count broken down by file extension.

9. Check if the repository has any files larger than 1 MB that are tracked in git. List any such files, because they may indicate accidentally committed binaries.

10. Scan the directory for all configuration files (`.yaml`, `.yml`, `.json`, `.toml`, `.ini`, `.cfg`). Check if each file is syntactically valid by reviewing its structure. Flag any that appear malformed.

11. Collect all flagged items and produce the report using the output contract below.

## Output Contract

Produce a Markdown report:

```markdown
# Repository Health Report

**Repository:** <name>
**Date:** <ISO 8601 date>
**Files checked:** <count>

## Summary

| Check | Result |
|-------|--------|
| Oversized files (>500 lines) | <count> |
| Markdown files missing headings | <count> |
| .gitignore present | Yes / No |
| README present | Yes / No |
| LICENSE present | Yes / No |
| TODO/FIXME comments | <count> |
| Files missing docstrings | <count> |
| Large tracked files (>1 MB) | <count> |

## Findings

<Bulleted list of all flagged items with file names and details.>

## Recommendations

<Bulleted list of recommended actions, ordered by severity.>
```

## Examples

**Example 1 — healthy repository:**

Input: A well-maintained Python library with 20 files.

Expected output: All summary checks show clean results except one TODO comment. Findings section is short. Recommendations section suggests resolving the TODO.

**Example 2 — repository with issues:**

Input: A repository with a 900-line module, three Markdown files without headings, and no LICENSE.

Expected output: Summary table shows counts for each issue. Findings lists each problem with the file name. Recommendations prioritise adding a LICENSE as the highest severity issue.

## Environment and Portability

No external tools required. All checks are performed by reading the file system and file contents available in context.

## References

No bundled files.
