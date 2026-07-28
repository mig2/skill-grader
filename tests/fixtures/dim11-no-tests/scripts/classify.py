#!/usr/bin/env python3
"""
classify.py — Classify a git diff into a conventional commit type.

Usage:
    classify.py --input <file>
    classify.py --input -     # read diff from stdin
    classify.py --help
"""

import argparse
import re
import sys
from pathlib import Path


COMMIT_TYPES = ["feat", "fix", "docs", "refactor", "test", "chore", "perf", "ci"]

# Heuristic keyword → commit type mappings
HEURISTICS = [
    (["test", "spec", "assert"], "test"),
    (["readme", ".md", "docstring", "comment"], "docs"),
    (["ci", "workflow", "github/workflows", ".github"], "ci"),
    (["setup.py", "pyproject.toml", "package.json", "makefile", "dockerfile"], "chore"),
    (["fix", "bug", "error", "exception", "crash", "typo", "correct"], "fix"),
    (["perf", "performance", "optimise", "optimize", "cache", "speed"], "perf"),
    (["refactor", "rename", "move", "restructure", "clean"], "refactor"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Classify a git diff into a conventional commit type.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--input",
        required=True,
        metavar="FILE",
        help="Path to diff file, or '-' to read from stdin.",
    )
    return parser.parse_args()


def read_diff(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def classify(diff: str) -> str:
    text = diff.lower()
    for keywords, commit_type in HEURISTICS:
        if any(kw in text for kw in keywords):
            return commit_type
    # Default to feat if new lines exceed removed lines
    added = len(re.findall(r"^\+[^+]", diff, re.MULTILINE))
    removed = len(re.findall(r"^-[^-]", diff, re.MULTILINE))
    return "feat" if added > removed else "chore"


def main() -> None:
    args = parse_args()
    diff = read_diff(args.input)
    result = classify(diff)
    print(result)


if __name__ == "__main__":
    main()
