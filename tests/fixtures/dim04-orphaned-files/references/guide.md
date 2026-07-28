# Commit Classification Guide

This guide defines how to classify git commits into changelog categories for the changelog-writer skill.

## Categories

### Breaking Changes

A commit is a breaking change if it:
- Removes a public API endpoint, function, method, or field
- Changes the signature or behavior of an existing API in a way that requires callers to update
- Changes the format of a configuration file or data format in a backward-incompatible way
- Renames a public interface

Conventional commit prefix: `feat!`, `fix!`, or any type with `!` suffix, or a `BREAKING CHANGE:` footer.

### New Features

A commit is a new feature if it:
- Adds a new capability that did not exist before
- Adds a new configuration option or mode
- Exposes a new API endpoint or function

Conventional commit prefix: `feat`.

### Bug Fixes

A commit is a bug fix if it:
- Corrects incorrect behavior
- Fixes a crash or error
- Resolves a security vulnerability (if the vulnerability was not intentional)

Conventional commit prefix: `fix`, `hotfix`.

### Maintenance

All other commits that are user-visible but not new features or bugs:
- Documentation updates
- Dependency version bumps
- Performance improvements with no API change
- Refactoring that changes no external behavior
- CI/build changes

Conventional commit prefix: `docs`, `chore`, `refactor`, `perf`, `ci`, `build`, `test`.

## Classification Heuristics for Non-Conventional Commits

If the project does not use conventional commits, classify by subject line keywords:

| Keywords | Category |
|----------|----------|
| "breaking", "incompatible", "remove support", "drop" | Breaking Changes |
| "add", "introduce", "implement", "support", "enable" | New Features |
| "fix", "correct", "resolve", "patch", "repair" | Bug Fixes |
| "update", "bump", "upgrade", "refactor", "clean" | Maintenance |

When in doubt, use Maintenance. Do not invent a new category.
