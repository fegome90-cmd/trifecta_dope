#!/usr/bin/env python3
"""Migrate existing WO YAML files to use Priority enum.

This script converts WO YAML files that have priority as a plain string
to use validated enum values. Run this before deploying enum changes
to maintain backwards compatibility.

Usage:
    uv run python scripts/migrate_priority_enum.py
    # Then commit the migrated YAML files
    git add _ctx/jobs/
    git commit -m "chore: migrate WO priority strings to enum values"
"""

import re
import sys
from enum import StrEnum
from pathlib import Path

import yaml


class Priority(StrEnum):
    """Valid priority levels for Work Orders."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Pattern for valid WO IDs (WO-XXXX format)
WO_ID_PATTERN = re.compile(r"^WO-\d{4}$", re.IGNORECASE)


def migrate_wo_file(yaml_path: Path, dry_run: bool = False) -> bool:
    """Migrate a single WO YAML file.

    Args:
        yaml_path: Path to the WO YAML file
        dry_run: If True, only report changes without writing

    Returns:
        True if migration was needed and successful, False otherwise
    """
    if not yaml_path.exists():
        print(f"WARNING: File not found: {yaml_path}")
        return False

    try:
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"ERROR: Invalid YAML in {yaml_path}: {e}")
        return False

    # Check if priority field exists and needs migration
    if "priority" not in data:
        return False  # No priority field, nothing to migrate

    old_priority = data["priority"]
    if not isinstance(old_priority, str):
        return False  # Already an enum or non-string type

    # Check if already a valid enum value
    if old_priority in Priority.__members__.values():
        return False  # Already valid, no migration needed

    # Try to normalize and validate the priority value
    try:
        # Case-insensitive matching
        normalized = old_priority.lower()
        if normalized not in [p.value for p in Priority]:
            raise ValueError(f"Invalid priority value: {old_priority}")

        data["priority"] = Priority(normalized).value

        if dry_run:
            print(f"[DRY RUN] Would migrate {yaml_path}: '{old_priority}' -> '{data['priority']}'")
            return True

        # Write back with sort_keys=False to preserve order
        yaml_path.write_text(yaml.safe_dump(data, sort_keys=False))
        print(f"✓ Migrated {yaml_path}: '{old_priority}' -> '{data['priority']}'")
        return True

    except ValueError as e:
        print(f"WARNING: Invalid priority '{old_priority}' in {yaml_path}: {e}")
        return False


def migrate_all(jobs_base: Path, dry_run: bool = False) -> int:
    """Migrate all WO YAML files in _ctx/jobs/.

    Args:
        jobs_base: Path to the jobs directory (_ctx/jobs/)
        dry_run: If True, only report changes without writing

    Returns:
        Number of files migrated
    """
    migrated = 0
    state_dirs = ["pending", "running", "done", "failed"]

    for state_dir in state_dirs:
        state_path = jobs_base / state_dir
        if not state_path.exists():
            continue

        yaml_files = list(state_path.glob("WO-*.yaml"))
        if not yaml_files:
            continue

        print(f"\nChecking {state_dir}/ ({len(yaml_files)} files)...")

        for yaml_file in yaml_files:
            if migrate_wo_file(yaml_file, dry_run):
                migrated += 1

    return migrated


def main() -> int:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Migrate WO priority strings to enum values"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing files"
    )
    parser.add_argument(
        "--jobs-dir",
        type=Path,
        default=Path("_ctx/jobs"),
        help="Path to jobs directory (default: _ctx/jobs/)"
    )
    args = parser.parse_args()

    if not args.jobs_dir.exists():
        print(f"ERROR: Jobs directory not found: {args.jobs_dir}")
        return 1

    print("=" * 60)
    print("WO Priority Migration Script")
    print("=" * 60)

    if args.dry_run:
        print("\n[DRY RUN MODE] - No files will be modified\n")

    migrated = migrate_all(args.jobs_dir, dry_run=args.dry_run)

    print("\n" + "=" * 60)
    if args.dry_run:
        print(f"Would migrate {migrated} WO file(s)")
    else:
        print(f"Migrated {migrated} WO file(s)")
    print("=" * 60)

    if args.dry_run and migrated > 0:
        print("\nRun without --dry-run to apply changes")
        return 2  # Exit code 2 indicates changes would be made

    return 0


if __name__ == "__main__":
    sys.exit(main())
