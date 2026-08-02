#!/usr/bin/env python3
"""Reconcile issues.md against GitHub and against git history.

Drift here is silent and easy to miss: an issue closed on GitHub but never
logged, a log entry for an issue that was reopened, or a run of commits with no
issue behind them at all. Each is invisible until someone reads both sources
side by side, which nobody does.

Read-only by default. Reports what disagrees and exits non-zero so it can gate
a commit; --json emits the same findings for tooling.

    uv run python scripts/sync_issues.py
    uv run python scripts/sync_issues.py --repo mig2/code-audit --path ~/Code/skill-audit
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# `### #12 — Title`
ENTRY = re.compile(r"^### #(\d+)\s+[—-]\s+(.*)$", re.MULTILINE)
# `- **Commit:** abc1234` / `- **Commits:** abc1234, def5678`
COMMITS = re.compile(r"^- \*\*Commits?:\*\*\s*(.+)$", re.MULTILINE)

# Commits that legitimately have no issue: bookkeeping of the log itself, and
# housekeeping. Matched loosely because repos differ on whether they use
# conventional-commit prefixes.
EXEMPT = re.compile(
    r"(record .*hash|log issue|close .*issues|^chore[:(]|^docs: (record|log))",
    re.IGNORECASE,
)


def _run(*args: str, cwd: Path | None = None) -> str:
    proc = subprocess.run(
        args, capture_output=True, text=True, cwd=cwd, timeout=30,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"{' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def parse_log(path: Path) -> dict[int, dict]:
    """Extract issue entries from issues.md, keyed by number."""
    text = path.read_text(encoding="utf-8")
    entries: dict[int, dict] = {}
    blocks = text.split("### #")
    for block in blocks[1:]:
        header = "### #" + block
        m = ENTRY.search(header)
        if not m:
            continue
        num = int(m.group(1))
        commits: list[str] = []
        cm = COMMITS.search(header)
        if cm:
            commits = [c.strip() for c in cm.group(1).split(",") if c.strip()]
        entries[num] = {"title": m.group(2).strip(), "commits": commits}
    return entries


def fetch_issues(repo: str) -> dict[int, dict]:
    out = _run(
        "gh", "issue", "list", "--repo", repo, "--state", "all",
        "--limit", "200", "--json", "number,title,state",
    )
    return {i["number"]: i for i in json.loads(out)}


def _is_logged(sha: str, logged: set[str]) -> bool:
    """Match on prefix — logs abbreviate hashes to varying lengths."""
    return any(sha.startswith(c) or c.startswith(sha) for c in logged)


def unlogged_commits(repo_path: Path, logged: set[str]) -> list[tuple[str, str]]:
    """Commits made since the most recently logged one, with no issue behind them.

    Deliberately does not audit all history. Entries commonly cite one
    representative hash for work spanning several commits, so treating every
    uncited commit as drift buries the real signal in settled history. What
    matters is whether work has happened since the log was last brought up to
    date.
    """
    out = _run("git", "log", "--pretty=%h\t%s", cwd=repo_path)
    lines = [l for l in out.splitlines() if l.strip()]

    since: list[tuple[str, str]] = []
    for line in lines:  # newest first
        sha, _, subject = line.partition("\t")
        if _is_logged(sha, logged):
            break  # reached the last logged commit; everything older is settled
        since.append((sha, subject))
    else:
        # No logged commit anywhere in history — no baseline to measure from.
        return []

    return [(s, m) for s, m in since if not EXEMPT.search(m)]


def reconcile(repo: str, repo_path: Path) -> list[dict]:
    log = parse_log(repo_path / "issues.md")
    gh = fetch_issues(repo)
    findings: list[dict] = []

    for num in sorted(set(gh) - set(log)):
        if gh[num]["state"] == "CLOSED":
            findings.append({
                "kind": "missing-log-entry",
                "detail": f"#{num} is closed on GitHub but absent from issues.md: {gh[num]['title']}",
            })

    for num in sorted(set(log) - set(gh)):
        findings.append({
            "kind": "orphan-log-entry",
            "detail": f"#{num} is logged in issues.md but does not exist on GitHub",
        })

    for num in sorted(set(log) & set(gh)):
        if gh[num]["state"] != "CLOSED":
            findings.append({
                "kind": "logged-but-open",
                "detail": f"#{num} is logged as closed but is {gh[num]['state']} on GitHub",
            })
        if not log[num]["commits"]:
            findings.append({
                "kind": "no-commit-reference",
                "detail": f"#{num} has no commit reference in issues.md",
            })

    logged_commits = {c for e in log.values() for c in e["commits"]}
    for sha, subject in unlogged_commits(repo_path, logged_commits):
        findings.append({
            "kind": "unlogged-commit",
            "detail": f"{sha} {subject}",
        })

    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default="mig2/skill-grader",
                    help="GitHub owner/name (default: mig2/skill-grader)")
    ap.add_argument("--path", default=".", type=Path,
                    help="Path to the local checkout (default: .)")
    ap.add_argument("--json", action="store_true", help="Emit findings as JSON")
    args = ap.parse_args()

    repo_path = args.path.expanduser().resolve()
    if not (repo_path / "issues.md").is_file():
        print(f"No issues.md in {repo_path}", file=sys.stderr)
        return 2

    try:
        findings = reconcile(args.repo, repo_path)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(findings, indent=2))
        return 1 if findings else 0

    if not findings:
        print(f"{args.repo}: issues.md, GitHub, and git history agree.")
        return 0

    by_kind: dict[str, list[str]] = {}
    for f in findings:
        by_kind.setdefault(f["kind"], []).append(f["detail"])

    print(f"{args.repo}: {len(findings)} discrepancies\n")
    for kind, details in by_kind.items():
        print(f"{kind} ({len(details)})")
        for d in details:
            print(f"  {d}")
        print()
    return 1


if __name__ == "__main__":
    sys.exit(main())
