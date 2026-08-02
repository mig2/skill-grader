---
name: changelog-builder
description: >
  Build a release changelog from merged pull requests between two git tags.
  Use when asked to write a changelog, draft release notes, or summarise what
  shipped in a release. Use when asked "what changed since v2.1?" or
  "prepare the release notes".
  Do NOT use for writing individual commit messages — that is a separate concern.
---

# Changelog Builder

Assemble a release changelog from the pull requests merged between two tags,
grouped by change type and ordered by user impact.

## Workflow

1. Run `scripts/collect_prs.py --from <tag> --to <tag>` to gather merged pull
   requests with their titles, labels, and authors. The script handles
   pagination and rate limiting, which are fiddly enough to be worth scripting
   rather than re-deriving each run.

2. Group the results by change type using the label mapping in
   `references/label-map.md`. Labels are the only reliable signal here — PR
   titles are too inconsistent to classify from text alone.

3. Order each group by user impact, not merge order. A one-line fix to a
   crash matters more to a reader than a large refactor they will never see.

4. Render using the template below.

## Output Contract

Emit exactly this structure:

```markdown
## <version> — <YYYY-MM-DD>

### Breaking changes
- <description> (#<pr-number>, @<author>)

### Features
- <description> (#<pr-number>, @<author>)

### Fixes
- <description> (#<pr-number>, @<author>)

### Internal
- <description> (#<pr-number>, @<author>)
```

Omit any section with no entries rather than printing an empty heading. Readers
scan headings first, and an empty one costs them a stop.

## Examples

**A feature PR titled "Add retry to the upload client", labelled `feature`:**

```markdown
### Features
- Upload client now retries transient failures (#412, @dana)
```

**A fix PR titled "fix npe", labelled `bug`:**

```markdown
### Fixes
- Fixed a crash when opening a document with no metadata (#418, @sam)
```

The second example matters more than the first: the PR title was useless, so
the entry was rewritten from the diff. Do not copy titles verbatim.

## Environment and Portability

Requires Python 3.9+ and the `gh` CLI authenticated against the target repo.
If `gh` is unavailable, `scripts/collect_prs.py` falls back to parsing
`git log --merges` output, which loses labels — in that case classify by
reading each merge commit and say so in the output.

## Bundled Files

| File | Purpose |
|------|---------|
| `scripts/collect_prs.py` | Gather merged PRs between two tags |
| `references/label-map.md` | Label to change-type mapping |
| `tests/test_collect_prs.py` | Unit tests for the collection script |
