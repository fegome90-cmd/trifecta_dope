#!/usr/bin/env python3
"""
WO Garbage Collection Script

Cleans up zombie and ghost worktrees to prevent accumulation.

Usage:
    uv run python scripts/ctx_wo_gc.py --dry-run
    uv run python scripts/ctx_wo_gc.py --apply
    uv run python scripts/ctx_wo_gc.py --apply --force  # Removes dirty worktrees

Exit codes:
    0: Success (no issues or all cleaned)
    1: Issues found (dry-run) or cleanup failed
    2: Invalid arguments or repo not found
"""

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class WorktreeInfo:
    """Information about a git worktree."""

    path: str
    head: str
    branch: str
    wo_id: str
    is_dirty: bool = False
    wo_state: str | None = None  # pending, running, done, failed, or None (ghost)


@dataclass
class GCReport:
    """Report of GC operations."""

    timestamp: str
    repo_root: str
    dry_run: bool
    zombies_found: int = 0
    ghosts_found: int = 0
    zombies_removed: int = 0
    ghosts_removed: int = 0
    zombies_skipped_dirty: int = 0
    errors: list[str] = field(default_factory=list)
    actions: list[dict[str, Any]] = field(default_factory=list)


CANONICAL_STATES = ["pending", "running", "done", "failed"]


def run_command(
    cmd: list[str], cwd: Path | None = None, check: bool = True
) -> subprocess.CompletedProcess:
    """Run a shell command."""
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=check,
    )


def get_worktrees(repo_root: Path) -> list[WorktreeInfo]:
    """Get list of all worktrees from git."""
    result = run_command(["git", "worktree", "list", "--porcelain"], cwd=repo_root)

    worktrees = []
    current_path = None
    current_head = None
    current_branch = None

    for line in result.stdout.strip().split("\n"):
        if line.startswith("worktree "):
            if current_path:
                wt_path = Path(current_path)
                wo_id = wt_path.name if wt_path.name.startswith("WO-") else "main"
                worktrees.append(
                    WorktreeInfo(
                        path=current_path,
                        head=current_head or "",
                        branch=current_branch or "",
                        wo_id=wo_id,
                    )
                )
            current_path = line[9:]
            current_head = None
            current_branch = None
        elif line.startswith("HEAD "):
            current_head = line[5:]
        elif line.startswith("branch "):
            current_branch = line[7:]

    # Don't forget the last one
    if current_path:
        wt_path = Path(current_path)
        wo_id = wt_path.name if wt_path.name.startswith("WO-") else "main"
        worktrees.append(
            WorktreeInfo(
                path=current_path,
                head=current_head or "",
                branch=current_branch or "",
                wo_id=wo_id,
            )
        )

    return worktrees


def get_wo_state(repo_root: Path, wo_id: str) -> str | None:
    """Get the state of a WO from YAML files."""
    for state in CANONICAL_STATES:
        yaml_path = repo_root / "_ctx" / "jobs" / state / f"{wo_id}.yaml"
        if yaml_path.exists():
            return state
    return None


def check_worktree_dirty(worktree_path: str) -> bool:
    """Check if a worktree has uncommitted changes."""
    try:
        result = run_command(
            ["git", "status", "--porcelain"],
            cwd=Path(worktree_path),
            check=False,
        )
        return bool(result.stdout.strip())
    except Exception:
        return False


def classify_worktrees(
    repo_root: Path, worktrees: list[WorktreeInfo]
) -> tuple[list[WorktreeInfo], list[WorktreeInfo]]:
    """Classify worktrees into zombies and ghosts."""
    zombies = []
    ghosts = []

    for wt in worktrees:
        if wt.wo_id == "main":
            continue

        # Get WO state
        wt.wo_state = get_wo_state(repo_root, wt.wo_id)

        # Check if dirty
        wt.is_dirty = check_worktree_dirty(wt.path)

        if wt.wo_state is None:
            # Ghost: worktree exists but no WO YAML
            ghosts.append(wt)
        elif wt.wo_state in ("done", "failed"):
            # Zombie: WO is done/failed but worktree still exists
            zombies.append(wt)

    return zombies, ghosts


def remove_worktree(repo_root: Path, wt: WorktreeInfo, force: bool) -> tuple[bool, str]:
    """Remove a worktree. Returns (success, message)."""
    try:
        if wt.is_dirty and not force:
            return False, f"Worktree {wt.wo_id} is dirty, use --force to remove"

        result = run_command(
            ["git", "worktree", "remove", wt.path] + (["--force"] if force else []),
            cwd=repo_root,
            check=False,
        )

        if result.returncode != 0:
            return False, f"Failed to remove {wt.wo_id}: {result.stderr.strip()}"

        return True, f"Removed worktree {wt.wo_id}"
    except Exception as e:
        return False, f"Exception removing {wt.wo_id}: {e}"


def run_gc(
    repo_root: Path, dry_run: bool = True, force: bool = False, json_path: str | None = None
) -> GCReport:
    """Run garbage collection on worktrees."""
    report = GCReport(
        timestamp=datetime.now(timezone.utc).isoformat(),
        repo_root=str(repo_root),
        dry_run=dry_run,
    )

    # Get all worktrees
    worktrees = get_worktrees(repo_root)

    # Classify into zombies and ghosts
    zombies, ghosts = classify_worktrees(repo_root, worktrees)

    report.zombies_found = len(zombies)
    report.ghosts_found = len(ghosts)

    # Process zombies
    for wt in zombies:
        if dry_run:
            action = {
                "type": "zombie",
                "wo_id": wt.wo_id,
                "path": wt.path,
                "wo_state": wt.wo_state,
                "is_dirty": wt.is_dirty,
                "action": "would_remove" if not wt.is_dirty or force else "would_skip_dirty",
            }
            report.actions.append(action)
            if wt.is_dirty and not force:
                report.zombies_skipped_dirty += 1
        else:
            success, message = remove_worktree(repo_root, wt, force)
            action = {
                "type": "zombie",
                "wo_id": wt.wo_id,
                "path": wt.path,
                "wo_state": wt.wo_state,
                "is_dirty": wt.is_dirty,
                "action": "removed" if success else "failed",
                "message": message,
            }
            report.actions.append(action)

            if success:
                report.zombies_removed += 1
            else:
                report.errors.append(message)
                if wt.is_dirty:
                    report.zombies_skipped_dirty += 1

    # Process ghosts
    for wt in ghosts:
        if dry_run:
            action = {
                "type": "ghost",
                "wo_id": wt.wo_id,
                "path": wt.path,
                "is_dirty": wt.is_dirty,
                "action": "would_remove" if not wt.is_dirty or force else "would_skip_dirty",
            }
            report.actions.append(action)
        else:
            success, message = remove_worktree(repo_root, wt, force)
            action = {
                "type": "ghost",
                "wo_id": wt.wo_id,
                "path": wt.path,
                "is_dirty": wt.is_dirty,
                "action": "removed" if success else "failed",
                "message": message,
            }
            report.actions.append(action)

            if success:
                report.ghosts_removed += 1
            else:
                report.errors.append(message)

    # Write JSON report if requested
    if json_path:
        report_dict = {
            "timestamp": report.timestamp,
            "repo_root": report.repo_root,
            "dry_run": report.dry_run,
            "summary": {
                "zombies_found": report.zombies_found,
                "ghosts_found": report.ghosts_found,
                "zombies_removed": report.zombies_removed,
                "ghosts_removed": report.ghosts_removed,
                "zombies_skipped_dirty": report.zombies_skipped_dirty,
                "errors_count": len(report.errors),
            },
            "actions": report.actions,
            "errors": report.errors,
        }
        Path(json_path).write_text(json.dumps(report_dict, indent=2))

    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="WO Garbage Collection - Clean up zombie and ghost worktrees"
    )
    parser.add_argument("--root", default=".", help="Repository root path")
    parser.add_argument("--dry-run", action="store_true", help="Report only, don't make changes")
    parser.add_argument("--apply", action="store_true", help="Apply cleanup (default is dry-run)")
    parser.add_argument("--force", action="store_true", help="Force removal of dirty worktrees")
    parser.add_argument("--json", dest="json_path", help="Write JSON report to file")

    args = parser.parse_args()

    repo_root = Path(args.root).resolve()
    if not repo_root.exists():
        print(f"ERROR: Repository root not found: {repo_root}", file=sys.stderr)
        return 2

    # Default to dry-run unless --apply is specified
    dry_run = not args.apply

    if dry_run:
        print("=== WO GC DRY-RUN MODE ===")
    else:
        print("=== WO GC APPLY MODE ===")

    print(f"Repository: {repo_root}")
    print()

    report = run_gc(
        repo_root=repo_root,
        dry_run=dry_run,
        force=args.force,
        json_path=args.json_path,
    )

    # Print summary
    print(f"Zombies found: {report.zombies_found}")
    print(f"  Removed: {report.zombies_removed}")
    print(f"  Skipped (dirty): {report.zombies_skipped_dirty}")
    print(f"Ghost worktrees found: {report.ghosts_found}")
    print(f"  Removed: {report.ghosts_removed}")

    if report.errors:
        print(f"\nErrors ({len(report.errors)}):")
        for err in report.errors:
            print(f"  - {err}")

    # Print actions
    if report.actions:
        print("\nActions:")
        for action in report.actions:
            wo_id = action.get("wo_id", "unknown")
            action_type = action.get("type", "unknown")
            act = action.get("action", "unknown")
            dirty = " (dirty)" if action.get("is_dirty") else ""
            print(f"  [{action_type}] {wo_id}: {act}{dirty}")

    # Write JSON report
    if args.json_path:
        print(f"\nJSON report written to: {args.json_path}")

    # Exit code
    if dry_run:
        # In dry-run, exit 1 if issues found (so CI can detect)
        return 1 if (report.zombies_found > 0 or report.ghosts_found > 0) else 0
    else:
        # In apply mode, exit 1 if any errors
        return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
