#!/usr/bin/env python3
"""
Add x_legacy_flow marker to historical WOs.

This script adds the x_legacy_flow: true marker to WOs that have
required_flow: [verify] instead of the full Trifecta flow.

See ADR-003 for rationale.
"""

import argparse
import re
from pathlib import Path
from typing import NamedTuple


class WOLegacyInfo(NamedTuple):
    """Information about a legacy WO."""

    path: Path
    wo_id: str
    has_legacy_flow: bool
    already_marked: bool


def find_legacy_wos(done_dir: Path) -> list[WOLegacyInfo]:
    """Find all WOs with legacy required_flow pattern."""
    legacy_wos = []

    for wo_file in done_dir.glob("*.yaml"):
        content = wo_file.read_text()

        # Check if has legacy flow pattern (required_flow: [verify] or partial flow)
        has_legacy_flow = bool(re.search(r"required_flow:\s*\n\s*-\s*verify\s*\n", content))

        # Also check for partial flow (only session.append:intent and ctx.sync)
        has_partial_flow = bool(
            re.search(
                r"required_flow:\s*\n\s*-\s*session\.append:intent\s*\n\s*-\s*ctx\.sync\s*\n",
                content,
            )
        )

        # Check if already has x_legacy_flow marker
        already_marked = "x_legacy_flow:" in content

        if (has_legacy_flow or has_partial_flow) and not already_marked:
            wo_id = wo_file.stem
            legacy_wos.append(
                WOLegacyInfo(
                    path=wo_file,
                    wo_id=wo_id,
                    has_legacy_flow=has_legacy_flow,
                    already_marked=False,
                )
            )

    return legacy_wos


def add_legacy_marker(wo_file: Path, dry_run: bool = True) -> bool:
    """Add x_legacy_flow: true marker to a WO file.

    Args:
        wo_file: Path to the WO YAML file
        dry_run: If True, only preview changes

    Returns:
        True if modification was made (or would be made in dry_run)
    """
    content = wo_file.read_text()

    # Find the execution block and add x_legacy_flow after required_flow
    # Pattern: required_flow:\n  - ...\n  segment: .
    # We want to add x_legacy_flow: true before segment

    pattern = r"(required_flow:\s*\n(?:\s*-\s*[^\n]+\n)+)(\s*segment:\s*\.)"

    def add_marker(match: re.Match) -> str:
        required_flow_block = match.group(1)
        segment_line = match.group(2)
        indent = "  "  # Standard 2-space indent
        return f"{required_flow_block}{indent}x_legacy_flow: true\n{segment_line}"

    new_content = re.sub(pattern, add_marker, content)

    if new_content == content:
        # No change made - pattern not found
        return False

    if dry_run:
        print(f"  [DRY-RUN] Would add x_legacy_flow to: {wo_file.name}")
        # Show the diff
        old_lines = content.split("\n")
        new_lines = new_content.split("\n")
        for i, (old, new) in enumerate(zip(old_lines, new_lines)):
            if old != new:
                print(f"    Line {i + 1}:")
                print(f"      - {old}")
                print(f"      + {new}")
        return True

    # Write the modified content
    wo_file.write_text(new_content)
    print(f"  ✓ Added x_legacy_flow to: {wo_file.name}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Add x_legacy_flow marker to historical WOs")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Preview changes without modifying files (default: True)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually modify files (overrides --dry-run)",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root directory (default: current directory)",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    done_dir = root / "_ctx/jobs" / "done"

    if not done_dir.exists():
        print(f"Error: Done directory not found: {done_dir}")
        return 1

    dry_run = not args.apply

    print(f"Scanning for legacy WOs in: {done_dir}")
    print(f"Mode: {'DRY-RUN (preview only)' if dry_run else 'APPLY (will modify files)'}")
    print()

    legacy_wos = find_legacy_wos(done_dir)

    if not legacy_wos:
        print("No legacy WOs found requiring x_legacy_flow marker.")
        return 0

    print(f"Found {len(legacy_wos)} legacy WOs:")
    for info in legacy_wos:
        print(f"  - {info.wo_id}")
    print()

    modified_count = 0
    for info in legacy_wos:
        if add_legacy_marker(info.path, dry_run=dry_run):
            modified_count += 1

    print()
    if dry_run:
        print(f"Summary: Would modify {modified_count} files")
        print("Run with --apply to actually modify files")
    else:
        print(f"Summary: Modified {modified_count} files")

    return 0


if __name__ == "__main__":
    exit(main())
