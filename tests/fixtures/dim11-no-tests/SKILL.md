---
name: commit-message-writer
version: 1.0.0
author: example-team
tags: [git, commit, writing]
---

# Commit Message Writer

## Description

Write a well-formed git commit message from a diff or description of changes. Use this skill when the user asks to write a commit message, generate a git commit, or draft a commit summary. Trigger on phrasings like "write a commit message", "generate a commit", "what should my commit message be", or "help me commit this". Do not trigger on requests to write changelogs or tag releases.

## When to Use

**Trigger conditions:**
- "Write a commit message for this diff"
- "Generate a commit message"
- "What should I put for the commit message?"
- "Help me commit these changes"
- "Draft a git commit for …"

**Do not trigger when:**
- The user asks to write a changelog (use changelog-writer skill)
- The user asks to tag or create a release
- The user asks to squash or rebase commits

## Instructions

1. Read the diff or change description provided by the user.

2. Identify the primary change type. Run `scripts/classify.py --input <diff>` to get a suggested type from: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `ci`.

3. Write the subject line: `<type>(<optional-scope>): <imperative-mood summary>`. The subject line must be 72 characters or fewer.

4. Write the body if the change is non-trivial. The body explains *why* the change was made, not *what* — the diff shows what. Wrap at 72 characters.

5. Add a footer if there are breaking changes (`BREAKING CHANGE: <description>`) or issue references (`Closes #<number>`).

6. Produce the output following the contract below.

## Output Contract

Produce the commit message as plain text (not Markdown):

```
<type>(<scope>): <subject>

<body — omit if trivial>

<footer — omit if not applicable>
```

The subject line must be 72 characters or fewer. Body lines must wrap at 72 characters. The scope is optional but must be lowercase and hyphenated if present.

## Examples

**Example 1 — simple bug fix:**

Input: A one-line diff fixing a null check.

Expected output:
```
fix(auth): guard against null user in session check
```

**Example 2 — feature with scope:**

Input: A diff adding a new export format to a reporting module.

Expected output:
```
feat(reporting): add CSV export to report generator

Previously only JSON was supported. CSV export is needed for
downstream spreadsheet workflows.
```

**Example 3 — breaking change:**

Input: A diff removing a deprecated API endpoint.

Expected output:
```
feat(api)!: remove deprecated v1/users endpoint

BREAKING CHANGE: The v1/users endpoint has been removed. Migrate
to v2/users before upgrading.
```

## Environment and Portability

Requires Python 3.9+ for `scripts/classify.py`. If Python is unavailable, classify the commit type manually based on the change description.

## Bundled Files

| File | Purpose |
|------|---------|
| `scripts/classify.py` | Classify the commit type from a diff |

## References

See `scripts/classify.py --help` for usage.
