#!/usr/bin/env python3
"""
Work Order requeue script for trifecta_dope.
Transitions WO from failed -> pending state.

This is the OFFICIAL entrypoint for requeuing failed WOs.
Manual YAML moves are NOT supported.

Contract:
    - Requires: WO-ID, --reason (mandatory)
    - Transitions: failed/<WO>.yaml -> pending/<WO>.yaml
    - Preserves: All existing WO fields
    - Adds: x_requeued_from, x_requeued_at, x_requeue_reason
    - Does NOT: Create worktree, create lock, or modify branch

Guardrails (fail-closed):
    - WO must exist in failed/
    - WO must NOT exist in running/
    - No active lock for WO
    - No duplicate state (WO in multiple directories)
    - YAML must be valid

Usage:
    python ctx_wo_requeue.py WO-0061 --reason "verify scoped fixed"
    python ctx_wo_requeue.py --list                    # List failed WOs
"""

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from helpers import logger

from paths import (
    get_wo_failed_path,
    get_wo_pending_path,
    get_wo_running_path,
    get_lock_path,
    repo_root,
)


def load_yaml(path: Path) -> dict:
    """Load YAML file safely."""
    return yaml.safe_load(path.read_text())


def write_yaml(path: Path, data: dict) -> None:
    """Write YAML file preserving order."""
    path.write_text(yaml.safe_dump(data, sort_keys=False))


def validate_wo_id(wo_id: str) -> bool:
    """Validate WO ID format."""
    return bool(re.match(r"^WO-[A-Za-z0-9.-]+$", wo_id))


def check_wo_state_consistency(root: Path, wo_id: str) -> tuple[bool, str | None]:
    """Check that WO exists in exactly one state directory.

    Returns:
        Tuple of (is_consistent, error_message)
    """
    failed_path = get_wo_failed_path(root, wo_id)
    pending_path = get_wo_pending_path(root, wo_id)
    running_path = get_wo_running_path(root, wo_id)

    locations = []
    if failed_path.exists():
        locations.append("failed")
    if pending_path.exists():
        locations.append("pending")
    if running_path.exists():
        locations.append("running")

    if len(locations) == 0:
        return False, f"WO {wo_id} not found in any state directory"

    if len(locations) > 1:
        return False, f"WO {wo_id} exists in multiple states: {', '.join(locations)}"

    return True, None


def check_no_active_lock(root: Path, wo_id: str) -> tuple[bool, str | None]:
    """Check that no active lock exists for WO.

    Returns:
        Tuple of (no_lock, error_message)
    """
    lock_path = get_lock_path(root, wo_id)

    if not lock_path.exists():
        return True, None

    # Read lock metadata
    try:
        content = lock_path.read_text()
        return False, f"Active lock exists for {wo_id}:\n{content}"
    except Exception as e:
        return False, f"Active lock exists for {wo_id} (cannot read: {e})"


def validate_yaml_integrity(path: Path, wo_id: str) -> tuple[bool, str | None]:
    """Validate YAML file is parseable and has correct ID.

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        data = load_yaml(path)
    except yaml.YAMLError as e:
        return False, f"Invalid YAML in {path}: {e}"
    except Exception as e:
        return False, f"Cannot read {path}: {e}"

    if not isinstance(data, dict):
        return False, f"YAML must be a dict, got {type(data).__name__}"

    yaml_id = data.get("id")
    if yaml_id != wo_id:
        return False, f"YAML id mismatch: expected {wo_id}, got {yaml_id}"

    return True, None


def add_requeue_metadata(wo_data: dict, reason: str) -> dict:
    """Add requeue traceability metadata to WO.

    Preserves all existing fields and adds:
        - x_requeued_from: "failed"
        - x_requeued_at: ISO timestamp
        - x_requeue_reason: user-provided reason
    """
    wo_data["x_requeued_from"] = "failed"
    wo_data["x_requeued_at"] = datetime.now(timezone.utc).isoformat()
    wo_data["x_requeue_reason"] = reason

    # Reset status to pending
    wo_data["status"] = "pending"

    # Clear running-specific fields if present
    wo_data.pop("started_at", None)
    wo_data.pop("owner", None)

    return wo_data


def requeue_wo(root: Path, wo_id: str, reason: str) -> tuple[bool, str | None]:
    """Execute the failed -> pending transition.

    Args:
        root: Repository root path
        wo_id: Work Order ID
        reason: User-provided reason for requeue

    Returns:
        Tuple of (success, error_message)
    """
    failed_path = get_wo_failed_path(root, wo_id)
    pending_path = get_wo_pending_path(root, wo_id)

    # Guardrail 1: Must exist in failed
    if not failed_path.exists():
        return False, f"WO {wo_id} not found in failed/"

    # Guardrail 2: State consistency
    consistent, consistency_error = check_wo_state_consistency(root, wo_id)
    if not consistent:
        # Check specific case: exists in running
        running_path = get_wo_running_path(root, wo_id)
        if running_path.exists():
            return False, f"WO {wo_id} exists in running/ - cannot requeue while running"
        return False, consistency_error

    # Guardrail 3: No active lock
    no_lock, lock_error = check_no_active_lock(root, wo_id)
    if not no_lock:
        return False, lock_error

    # Guardrail 4: YAML integrity
    yaml_valid, yaml_error = validate_yaml_integrity(failed_path, wo_id)
    if not yaml_valid:
        return False, yaml_error

    # Load WO data
    wo_data = load_yaml(failed_path)

    # Add requeue metadata
    wo_data = add_requeue_metadata(wo_data, reason)

    # Atomic move: write to pending, then remove from failed
    try:
        write_yaml(pending_path, wo_data)
        failed_path.unlink()
    except Exception as e:
        # Attempt cleanup on failure
        if pending_path.exists():
            pending_path.unlink()
        return False, f"Failed to move WO: {e}"

    return True, None


def list_failed_wos(root: Path) -> None:
    """List all failed work orders."""
    failed_dir = root / "_ctx" / "jobs" / "failed"

    if not failed_dir.exists():
        print("No failed directory found.")
        return

    failed_wos = sorted(failed_dir.glob("WO-*.yaml"))

    if not failed_wos:
        print("No failed work orders.")
        return

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("   Failed Work Orders (requeueable)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    for wo_file in failed_wos:
        try:
            wo_data = load_yaml(wo_file)
            priority = wo_data.get("priority", "?")
            title = wo_data.get("title", wo_data.get("id", ""))
            print(f"  {wo_file.stem} [{priority}] - {title}")
        except Exception:
            print(f"  {wo_file.stem} [?] - (unreadable)")

    print(f"\nTotal: {len(failed_wos)}")
    print("\nTo requeue: python scripts/ctx_wo_requeue.py <WO-ID> --reason \"<reason>\"")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Requeue a failed work order to pending state",
        epilog="""
Examples:
  python ctx_wo_requeue.py WO-0061 --reason "verify scoped fixed"
  python ctx_wo_requeue.py --list
        """,
    )
    parser.add_argument("wo_id", nargs="?", help="Work order id, e.g. WO-0061")
    parser.add_argument(
        "--reason",
        required=False,
        help="Reason for requeue (mandatory when WO-ID provided)",
    )
    parser.add_argument("--root", default=".", help="Repo root (default: current directory)")
    parser.add_argument("--list", action="store_true", help="List failed work orders")

    args = parser.parse_args()

    # Handle --list flag
    if args.list:
        root = Path(args.root).resolve()
        list_failed_wos(root)
        return 0

    # Validate WO-ID provided
    if not args.wo_id:
        parser.print_help()
        return 1

    # Validate --reason provided
    if not args.reason:
        logger.error("--reason is mandatory for requeue")
        logger.error("Example: python ctx_wo_requeue.py WO-0061 --reason \"verify scoped fixed\"")
        return 1

    wo_id = args.wo_id
    root = Path(args.root).resolve()

    # Validate WO ID format
    if not validate_wo_id(wo_id):
        logger.error(f"Invalid WO ID format: {wo_id} (expected: WO-<alphanumeric>)")
        return 1

    # Execute requeue
    logger.info(f"Requeuing {wo_id} from failed to pending...")
    logger.info(f"  Reason: {args.reason}")

    success, error = requeue_wo(root, wo_id, args.reason)

    if not success:
        logger.error(f"Requeue failed: {error}")
        return 1

    # Success output
    pending_path = get_wo_pending_path(root, wo_id)

    print("\n" + "━" * 50)
    print(f"   ✅ Work Order {wo_id} Requeued Successfully")
    print("━" * 50)
    print(f"  WO ID:     {wo_id}")
    print(f"  From:      failed/")
    print(f"  To:        pending/")
    print(f"  Reason:    {args.reason}")
    print(f"  File:      {pending_path}")
    print("\nNext steps:")
    print(f"  1. python scripts/ctx_wo_take.py {wo_id}")
    print(f"  2. cd <worktree>")

    return 0


if __name__ == "__main__":
    sys.exit(main())
