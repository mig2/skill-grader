#!/usr/bin/env python3
"""Collect merged pull requests between two git tags."""

import argparse
import json
import subprocess


def collect(from_tag: str, to_tag: str) -> list[dict]:
    """Return merged PRs between two tags, newest first."""
    proc = subprocess.run(
        ["gh", "pr", "list", "--state", "merged", "--limit", "200",
         "--json", "number,title,labels,author"],
        capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0:
        return _fallback_from_git_log(from_tag, to_tag)
    return json.loads(proc.stdout or "[]")


def _fallback_from_git_log(from_tag: str, to_tag: str) -> list[dict]:
    """Parse merge commits when gh is unavailable. Loses label data."""
    proc = subprocess.run(
        ["git", "log", "--merges", "--pretty=%s", f"{from_tag}..{to_tag}"],
        capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0:
        return []
    return [
        {"number": None, "title": line, "labels": [], "author": None}
        for line in proc.stdout.splitlines()
        if line.strip()
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from", dest="from_tag", required=True)
    parser.add_argument("--to", dest="to_tag", required=True)
    args = parser.parse_args()
    print(json.dumps(collect(args.from_tag, args.to_tag), indent=2))


if __name__ == "__main__":
    main()
