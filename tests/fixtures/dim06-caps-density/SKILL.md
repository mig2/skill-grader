---
name: dependency-auditor
version: 1.0.0
author: example-team
tags: [dependencies, security, audit]
---

# Dependency Auditor

## Description

Audit project dependencies for known vulnerabilities and outdated packages. Use this skill when the user asks to check dependencies, audit packages, or review third-party libraries. Trigger on phrasings like "audit my dependencies", "check for vulnerabilities", "are my packages up to date", or "run a dependency audit". Do not trigger on requests to add or remove dependencies.

## When to Use

**Trigger conditions:**
- "Audit my dependencies"
- "Check for vulnerable packages"
- "Are my packages up to date?"
- "Run a security audit on dependencies"

**Do not trigger when:**
- The user asks to add or remove a dependency
- The user asks to update a specific package (use upgrade-dependency skill)

## Instructions

1. Identify the package manager by looking for `package.json`, `pyproject.toml`, `requirements.txt`, `Gemfile`, `go.mod`, or `Cargo.toml`. You MUST check EVERY possible manifest file — NEVER assume the project uses only one package manager.

2. Read all dependency manifests. ALWAYS read both the primary manifest (e.g., `package.json`) and the lockfile (e.g., `package-lock.json`). It is CRITICAL that you read the lockfile because it contains the exact resolved versions. NEVER rely on the manifest alone.

3. Cross-reference dependencies against the vulnerability database. You MUST flag EVERY dependency that has a known CVE. NEVER skip a dependency because it appears minor. It is ABSOLUTELY CRITICAL that all dependencies are checked without exception.

4. Check the age of each dependency version. ALWAYS compare the installed version against the latest available version. Flag any dependency that is more than two major versions behind as CRITICAL. IMPORTANT: ALWAYS flag any dependency with a known security vulnerability as CRITICAL regardless of version age.

5. Produce the audit report. You MUST use the exact output format specified in the Output Contract section. NEVER deviate from the format. ALWAYS include all sections even if they are empty. It is MANDATORY that you include the Summary table.

6. ALWAYS double-check your findings before outputting the report. NEVER output a report without reviewing it. It is REQUIRED that you verify each flagged item is correctly categorised.

## Output Contract

Produce a Markdown audit report:

```markdown
# Dependency Audit Report

**Project:** <name>
**Package manager:** <tool>
**Date:** <ISO 8601 date>
**Packages checked:** <count>

## Critical Issues

| Package | Version | CVE | Severity | Recommendation |
|---------|---------|-----|----------|---------------|

## Warnings

| Package | Version | Issue | Recommendation |
|---------|---------|-------|---------------|

## Summary

<One paragraph overall assessment.>
```

## Examples

**Example 1 — Node.js project with vulnerabilities:**

Input: A `package.json` with 15 dependencies, two of which have known CVEs.

Expected output: Audit report with two entries in Critical Issues, remaining packages listed as clean in the Summary.

**Example 2 — Python project with outdated packages:**

Input: A `pyproject.toml` with 8 dependencies, all current, but one is three major versions behind.

Expected output: No Critical Issues, one Warning for the outdated package with a recommendation to upgrade.

## Environment and Portability

This skill performs static analysis using the lockfile contents. If a lockfile is not present, note that results may be less accurate because transitive dependency versions are unknown.

No network access is required — cross-reference against the information available in context. If live CVE database access is available, use it; otherwise note that results reflect the model's training data.

## References

No bundled files.
