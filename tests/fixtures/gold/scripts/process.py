#!/usr/bin/env python3
"""
process.py — Extract structured metadata from a document for the document-summariser skill.

Usage:
    process.py --input <file> --type <type>
    process.py --input - --type <type>   # read from stdin
    process.py --help
"""

import argparse
import json
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract metadata from a document.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--input",
        required=True,
        metavar="FILE",
        help="Path to input file, or '-' to read from stdin.",
    )
    parser.add_argument(
        "--type",
        required=True,
        choices=["report", "article", "meeting-notes", "specification", "other"],
        help="Document type as classified by guide.md.",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        help="Write JSON output to FILE instead of stdout.",
    )
    return parser.parse_args()


def read_document(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def count_words(text: str) -> int:
    return len(text.split())


def extract_headers(text: str) -> list[str]:
    return [
        line.lstrip("#").strip()
        for line in text.splitlines()
        if re.match(r"^#{1,6}\s", line)
    ]


def extract_entities(text: str) -> dict[str, list[str]]:
    """Extract rough entity candidates using simple heuristics."""
    urls = re.findall(r"https?://\S+", text)
    emails = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
    return {
        "urls": list(dict.fromkeys(urls)),
        "emails": list(dict.fromkeys(emails)),
    }


def main() -> None:
    args = parse_args()
    text = read_document(args.input)

    result = {
        "word_count": count_words(text),
        "document_type": args.type,
        "section_headers": extract_headers(text),
        "entities": extract_entities(text),
    }

    output = json.dumps(result, indent=2)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output)


if __name__ == "__main__":
    main()
