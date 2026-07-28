# Changelog Formatting Style Guide

This file contains additional formatting guidance for changelog entries. It is not referenced by SKILL.md and exists as an orphaned resource.

## Header Format

Use `## [version] — date` with an em dash (—), not a hyphen (-).

## Link Definitions

If the project publishes changelogs to a web page, add link definitions at the bottom of CHANGELOG.md:

```markdown
[1.2.3]: https://github.com/org/repo/compare/v1.2.2...v1.2.3
```

## Keeping an Unreleased Section

Some projects maintain an `## [Unreleased]` section at the top of CHANGELOG.md. If the project follows this convention, move items from Unreleased to the version section when cutting a release.
