#!/usr/bin/env python3
"""
WO Evidence Retention GC Script

Cleans up old evidence files in _ctx/handoff/ while preserving recent work
and protecting active WOs.

Usage:
    uv run python scripts/wo_retention_gc.py --dry-run
    uv run python scripts/wo_retention_gc.py --dry-run --days 30
    uv run python scripts/wo_retention_gc.py --apply --days 90

Retention Policy:
    - Default retention: 90 days
    - Only targets: dirty.*.patch, dirty.patch.sha256
    - NEVER deletes: decision.md, handoff.md, verdict.json, diff.patch
    - NEVER deletes if WO is in running/ or pending/ state
    - NEVER deletes if decision.md is incomplete (status = ACTION_REQUIRED)

Exit codes:
    0: Success (no issues or all cleaned)
    1: Issues found (dry-run) or cleanup failed
    2: Invalid arguments or repo not found
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


@dataclass
class RetentionReport:
    """Report of retention GC operations."""

    timestamp: str
    repo_root: str
    dry_run: bool
    retention_days: int
    handoff_dir: str
    files_scanned: int = 0
    files_eligible: int = 0
    files_deleted: int = 0
    files_protected_active: int = 0
    files_protected_incomplete: int = 0
    bytes_freed: int = 0
    errors: list[str] = field(default_factory=list)
    actions: list[dict[str, Any]] = field(default_factory=list)
    protected_wos: list[str] = field(default_factory=list)
    deleted_files: list[str] = field(default_factory=list)


# Files that are eligible for retention cleanup
ELIGIBLE_PATTERNS = [
    "dirty.*.patch",  # Hashed patch files
    "dirty.patch.sha256",  # Checksum files
]

# Files that are NEVER deleted (protected)
PROTECTED_FILES = [
    "decision.md",
    "handoff.md",
    "verdict.json",
    "diff.patch",
    "dirty.patch",  # Symlink is preserved, only hashed files are deleted
]

# States that indicate active WO (protected from cleanup)
ACTIVE_STATES = ["running", "pending"]


def get_active_wo_ids(repo_root: Path) -> set[str]:
    """Get set of WO IDs that are in active states (running/pending)."""
    active_ids: set[str] = set()

    for state in ACTIVE_STATES:
        state_dir = repo_root / "_ctx" / "jobs" / state
        if state_dir.exists():
            for yaml_file in state_dir.glob("WO-*.yaml"):
                wo_id = yaml_file.stem
                active_ids.add(wo_id)

    return active_ids


def is_decision_incomplete(handoff_dir: Path) -> bool:
    """Check if decision.md exists and is incomplete (ACTION_REQUIRED status)."""
    decision_path = handoff_dir / "decision.md"

    if not decision_path.exists():
        # No decision.md means no incomplete decision to protect
        return False

    content = decision_path.read_text()

    # Check for incomplete status markers
    incomplete_markers = [
        "ACTION_REQUIRED",
        "[ ] APPLY",
        "[ ] DISCARD",
        "[ ] MANUAL REVIEW",
    ]

    # If any incomplete marker is found, the decision is incomplete
    for marker in incomplete_markers:
        if marker in content:
            return True

    return False


def get_file_age_days(file_path: Path) -> int:
    """Get the age of a file in days based on modification time."""
    mtime = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
    age = datetime.now(timezone.utc) - mtime
    return age.days


def is_eligible_for_cleanup(file_path: Path) -> bool:
    """Check if a file matches the eligible patterns for cleanup."""
    name = file_path.name

    # Check for hashed patch files (dirty.<hash>.patch)
    if name.startswith("dirty.") and name.endswith(".patch") and name != "dirty.patch":
        return True

    # Check for checksum files
    if name == "dirty.patch.sha256":
        return True

    return False


def run_retention_gc(
    repo_root: Path,
    dry_run: bool = True,
    retention_days: int = 90,
    json_path: str | None = None,
) -> RetentionReport:
    """Run retention garbage collection on handoff evidence.

    Args:
        repo_root: Repository root path
        dry_run: If True, only report what would be done
        retention_days: Minimum age in days for files to be eligible
        json_path: Optional path to write JSON report
    """
    report = RetentionReport(
        timestamp=datetime.now(timezone.utc).isoformat(),
        repo_root=str(repo_root),
        dry_run=dry_run,
        retention_days=retention_days,
        handoff_dir=str(repo_root / "_ctx" / "handoff"),
    )

    handoff_dir = repo_root / "_ctx" / "handoff"

    if not handoff_dir.exists():
        # No handoff directory, nothing to do
        return report

    # Get active WO IDs (protected from cleanup)
    active_wo_ids = get_active_wo_ids(repo_root)

    # Process each WO directory in handoff
    for wo_dir in handoff_dir.iterdir():
        if not wo_dir.is_dir():
            continue

        if not wo_dir.name.startswith("WO-"):
            continue

        wo_id = wo_dir.name

        # Check if WO is active (running/pending)
        if wo_id in active_wo_ids:
            report.protected_wos.append(wo_id)
            report.files_protected_active += 1
            continue

        # Check if decision is incomplete
        if is_decision_incomplete(wo_dir):
            report.files_protected_incomplete += 1
            report.protected_wos.append(f"{wo_id} (incomplete decision)")
            continue

        # Scan for eligible files
        for file_path in wo_dir.iterdir():
            if not file_path.is_file():
                continue

            report.files_scanned += 1

            # Skip protected files
            if file_path.name in PROTECTED_FILES:
                continue

            # Check if eligible for cleanup
            if not is_eligible_for_cleanup(file_path):
                continue

            # Check file age
            file_age = get_file_age_days(file_path)

            if file_age < retention_days:
                continue

            # File is eligible for cleanup
            file_size = file_path.stat().st_size
            report.files_eligible += 1

            action = {
                "wo_id": wo_id,
                "file": str(file_path.relative_to(repo_root)),
                "size_bytes": file_size,
                "age_days": file_age,
                "action": "would_delete" if dry_run else "deleted",
            }

            if dry_run:
                report.actions.append(action)
            else:
                try:
                    file_path.unlink()
                    report.files_deleted += 1
                    report.bytes_freed += file_size
                    report.deleted_files.append(str(file_path.relative_to(repo_root)))
                    report.actions.append(action)
                except Exception as e:
                    error_msg = f"Failed to delete {file_path}: {e}"
                    report.errors.append(error_msg)
                    action["action"] = "failed"
                    action["error"] = str(e)
                    report.actions.append(action)

    # Write JSON report if path provided
    if json_path:
        json_path_obj = Path(json_path)
        json_path_obj.parent.mkdir(parents=True, exist_ok=True)

        report_dict = {
            "timestamp": report.timestamp,
            "repo_root": report.repo_root,
            "dry_run": report.dry_run,
            "retention_days": report.retention_days,
            "summary": {
                "files_scanned": report.files_scanned,
                "files_eligible": report.files_eligible,
                "files_deleted": report.files_deleted,
                "files_protected_active": report.files_protected_active,
                "files_protected_incomplete": report.files_protected_incomplete,
                "bytes_freed": report.bytes_freed,
            },
            "protected_wos": report.protected_wos,
            "deleted_files": report.deleted_files,
            "errors": report.errors,
            "actions": report.actions,
        }

        json_path_obj.write_text(json.dumps(report_dict, indent=2))

    return report


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="WO Evidence Retention GC - Clean up old handoff evidence files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Dry run (default) - see what would be deleted
    uv run python scripts/wo_retention_gc.py --dry-run

    # Dry run with custom retention period
    uv run python scripts/wo_retention_gc.py --dry-run --days 30

    # Apply cleanup with 90-day retention
    uv run python scripts/wo_retention_gc.py --apply --days 90

    # Write JSON report
    uv run python scripts/wo_retention_gc.py --dry-run --json data/wo_retention_report.json
        """,
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Only report what would be deleted (default: True)",
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually delete files (default: False)",
    )

    parser.add_argument(
        "--days",
        type=int,
        default=90,
        help="Minimum age in days for files to be eligible (default: 90)",
    )

    parser.add_argument(
        "--json",
        type=str,
        default=None,
        help="Path to write JSON report",
    )

    args = parser.parse_args()

    # Determine dry_run mode
    dry_run = not args.apply

    # Find repo root
    try:
        result = __import__("subprocess").run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        repo_root = Path(result.stdout.strip())
    except Exception:
        print("ERROR: Could not find git repository root", file=sys.stderr)
        return 2

    # Run retention GC
    report = run_retention_gc(
        repo_root=repo_root,
        dry_run=dry_run,
        retention_days=args.days,
        json_path=args.json,
    )

    # Print summary
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("   WO Evidence Retention GC")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"Timestamp:     {report.timestamp}")
    print(f"Mode:          {'DRY RUN' if dry_run else 'APPLY'}")
    print(f"Retention:     {report.retention_days} days")
    print(f"Handoff dir:   {report.handoff_dir}")
    print("")
    print("Summary:")
    print(f"  Files scanned:           {report.files_scanned}")
    print(f"  Files eligible:          {report.files_eligible}")
    print(f"  Files deleted:           {report.files_deleted}")
    print(f"  Protected (active):      {report.files_protected_active}")
    print(f"  Protected (incomplete):  {report.files_protected_incomplete}")
    print(f"  Bytes freed:             {report.bytes_freed:,}")
    print("")

    if report.protected_wos:
        print("Protected WOs:")
        for wo in report.protected_wos:
            print(f"  - {wo}")
        print("")

    if report.errors:
        print("Errors:")
        for error in report.errors:
            print(f"  - {error}")
        print("")

    if report.actions:
        print("Actions:")
        for action in report.actions:
            status = "✓" if action["action"] == "deleted" else "○"
            if action["action"] == "failed":
                status = "✗"
            print(
                f"  {status} {action['file']} ({action['age_days']} days, {action['size_bytes']:,} bytes)"
            )
        print("")

    if args.json:
        print(f"JSON report: {args.json}")
        print("")

    # Exit code
    if report.errors:
        print("❌ Completed with errors")
        return 1

    if dry_run and report.files_eligible > 0:
        print(f"ℹ️  DRY RUN: {report.files_eligible} files would be deleted")
        return 0

    print("✅ Retention GC complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
