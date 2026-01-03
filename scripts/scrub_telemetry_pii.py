#!/usr/bin/env python3
"""Scrub PII from telemetry events.jsonl.

This script rewrites events.jsonl to replace absolute paths with <ABS_PATH_REDACTED>.
Useful for cleaning legacy telemetry that was created before PII sanitization.

Usage:
    python scripts/scrub_telemetry_pii.py ./_ctx/telemetry/events.jsonl
"""

import re
import sys
from pathlib import Path


# PII patterns to redact (order matters: process URIs first to avoid double-redaction)
PII_PATTERNS = [
    (re.compile(r'file:///[^"\s]+'), "<ABS_URI_REDACTED>"),
    (re.compile(r'/Users/[^"\s]+'), "<ABS_PATH_REDACTED>"),
    (re.compile(r'/home/[^"\s]+'), "<ABS_PATH_REDACTED>"),
    (re.compile(r'/private/var/[^"\s]+'), "<ABS_PATH_REDACTED>"),
    (re.compile(r'/mnt/[cC]/Users/[^"\s]+'), "<ABS_PATH_REDACTED>"),
    (re.compile(r'[A-Za-z]:\\\\Users\\\\[^"\s]+'), "<ABS_PATH_REDACTED>"),
]


def scrub_line(line: str) -> tuple[str, bool]:
    """Scrub PII from a single JSONL line.

    Returns:
        (scrubbed_line, was_modified)
    """
    modified = False
    scrubbed = line

    for pattern, replacement in PII_PATTERNS:
        if pattern.search(scrubbed):
            scrubbed = pattern.sub(replacement, scrubbed)
            modified = True

    return scrubbed, modified


def scrub_file(filepath: Path) -> dict:
    """Scrub PII from events.jsonl file.

    Returns:
        dict with keys: lines_scanned, lines_modified, backup_path
    """
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    # Create backup
    backup_path = filepath.with_suffix(".jsonl.bak")
    filepath.rename(backup_path)

    lines_scanned = 0
    lines_modified = 0

    # Read from backup, write scrubbed version to original path
    with open(backup_path, "r") as in_file, open(filepath, "w") as out_file:
        for line in in_file:
            lines_scanned += 1

            if not line.strip():
                out_file.write(line)
                continue

            scrubbed, modified = scrub_line(line)
            out_file.write(scrubbed)

            if modified:
                lines_modified += 1

    return {
        "lines_scanned": lines_scanned,
        "lines_modified": lines_modified,
        "backup_path": str(backup_path),
    }


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path/to/events.jsonl>", file=sys.stderr)
        sys.exit(1)

    filepath = Path(sys.argv[1])

    try:
        result = scrub_file(filepath)

        print(f"✅ Scrubbed {filepath}")
        print(f"   Lines scanned: {result['lines_scanned']}")
        print(f"   Lines modified: {result['lines_modified']}")
        print(f"   Backup created: {result['backup_path']}")

        if result["lines_modified"] == 0:
            print("\n   No PII patterns found (file was already clean)")
        else:
            print(f"\n   🔒 Redacted PII in {result['lines_modified']} lines")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
