---
name: changelog-writer
version: 1.0.0
author: example-team
tags: [changelog, release, documentation]
---

# Changelog Writer

## Description

Generate a formatted changelog entry from git commit history. Use this skill when the user asks to write a changelog, generate release notes, or document what changed in a version. Trigger on phrasings like "write the changelog", "generate release notes", "what changed since last release", or "update CHANGELOG.md". Do not trigger on requests to write commit messages or tag releases.

## When to Use

**Trigger conditions:**
- "Write the changelog for v<version>"
- "Generate release notes"
- "What changed since <tag>?"
- "Update CHANGELOG.md"
- "Summarise the commits since last release"

**Do not trigger when:**
- The user asks to write a git commit message (use commit-message skill)
- The user asks to tag or publish a release (use release skill)

## Instructions

1. Identify the version range. If the user specifies a version, use it. Otherwise, find the latest git tag and treat everything since that tag as the current release.

2. Run `git log <previous-tag>..HEAD --oneline --no-merges` to get the commit list.

3. Classify each commit into a category. Refer to `references/guide.md` for the classification rules and category definitions.

4. Within each category, sort commits by importance (breaking changes first, then new features, then fixes).

5. Write the changelog entry using the output contract below.

6. Prepend the new entry to `CHANGELOG.md` if the file exists. If not, create it with the new entry as the first content.

## Output Contract

Produce a Markdown changelog entry in this format:

```markdown
## [<version>] — <ISO 8601 date>

### Breaking Changes

- <description> (<short commit hash>)

### New Features

- <description> (<short commit hash>)

### Bug Fixes

- <description> (<short commit hash>)

### Maintenance

- <description> (<short commit hash>)
```

Omit any section that has no entries. Do not include a section heading if it would be empty.

## Examples

**Example 1 — patch release:**

Input: Five commits since last tag, all bug fixes and one dependency update.

Expected output: Entry with only `### Bug Fixes` and `### Maintenance` sections. Breaking Changes and New Features sections are omitted.

**Example 2 — minor release:**

Input: Twelve commits including two new features, three bug fixes, and a README update.

Expected output: Entry with `### New Features`, `### Bug Fixes`, and `### Maintenance`. No `### Breaking Changes`.

**Example 3 — major release:**

Input: Twenty commits including one breaking API change, several new features, and various fixes.

Expected output: All four sections present. Breaking change listed first with a clear description of the incompatibility.

## Environment and Portability

Requires git to be installed and the current directory to be a git repository. If git is unavailable, ask the user to provide the commit list as text input.

## References

See `references/guide.md` for commit classification rules.
