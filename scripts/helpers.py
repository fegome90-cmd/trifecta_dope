#!/usr/bin/env python3
"""
Helpers module for trifecta_dope orchestration scripts.
Provides common utilities for worktree management, git operations, and logging.
"""

import getpass
import logging
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# YAML import for rollback operations
import yaml

# Configuration constants
WORKTREE_BASE = ".worktrees"
BRANCH_PREFIX = "feat/wo"
DEFAULT_BRANCH = "main"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


def get_branch_name(wo_id: str) -> str:
    """
    Generate branch name from work order ID.
    Example: WO-0012 -> feat/wo-0012

    Args:
        wo_id: Work order ID (e.g., "WO-0012")

    Returns:
        Branch name (e.g., "feat/wo-0012")
    """
    return f"{BRANCH_PREFIX}-{wo_id}"


def get_worktree_path(wo_id: str, root: Path) -> Path:
    """
    Generate worktree path from work order ID.
    Example: WO-0012 -> .worktrees/WO-0012

    Args:
        wo_id: Work order ID (e.g., "WO-0012")
        root: Repository root path

    Returns:
        Worktree path (e.g., Path(".worktrees/WO-0012"))
    """
    return (root / WORKTREE_BASE / wo_id).resolve()


def run_command(cmd: list[str], cwd: Optional[Path] = None, check: bool = True) -> subprocess.CompletedProcess:
    """
    Run a shell command with error handling.

    Args:
        cmd: Command and arguments as list
        cwd: Working directory (defaults to current)
        check: Whether to raise exception on non-zero exit

    Returns:
        CompletedProcess with result
    """
    logger.debug(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=check,
            capture_output=True,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {' '.join(cmd)}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        raise


def git_get_current_branch(root: Path) -> str:
    """Get current git branch name."""
    result = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=root)
    return result.stdout.strip()


def git_get_default_branch(root: Path) -> str:
    """Get default branch (main/master)."""
    # Try to get the default branch from origin
    try:
        result = run_command(
            ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
            cwd=root,
            check=False
        )
        if result.returncode == 0:
            return result.stdout.strip().split("/")[-1]
    except Exception:
        pass

    # Fallback: check if main or master exists
    for branch in ["main", "master"]:
        result = run_command(
            ["git", "rev-parse", "--verify", branch],
            cwd=root,
            check=False
        )
        if result.returncode == 0:
            return branch

    # Ultimate fallback
    return DEFAULT_BRANCH


def create_worktree(
    root: Path,
    wo_id: str,
    branch: Optional[str] = None,
    worktree_path: Optional[Path] = None
) -> tuple[str, Path]:
    """
    Create a git worktree for the given work order.

    If branch or worktree_path are not provided, they are generated automatically:
    - branch: feat/wo-WO-XXXX
    - worktree: .worktrees/WO-XXXX

    Args:
        root: Repository root path
        wo_id: Work order ID (e.g., "WO-0012")
        branch: Branch name (auto-generated if None)
        worktree_path: Worktree path (auto-generated if None)

    Returns:
        Tuple of (branch_name, worktree_path)

    Raises:
        subprocess.CalledProcessError: If git commands fail
    """
    # Generate defaults if not provided
    if branch is None:
        branch = get_branch_name(wo_id)
        logger.info(f"Auto-generated branch name: {branch}")

    if worktree_path is None:
        worktree_path = get_worktree_path(wo_id, root)
        logger.info(f"Auto-generated worktree path: {worktree_path}")

    # Check if worktree already exists
    if worktree_path.exists():
        logger.warning(f"Worktree already exists: {worktree_path}")
        # Check if it's registered with git
        result = run_command(["git", "worktree", "list"], cwd=root, check=False)
        if str(worktree_path) in result.stdout:
            logger.info(f"Worktree {worktree_path} is already registered with git")
            return branch, worktree_path
        # Otherwise, clean it up and recreate
        logger.info(f"Removing stale worktree directory: {worktree_path}")
        os.rmdir(worktree_path)

    # Get the base branch for the new worktree
    default_branch = git_get_default_branch(root)

    # Check if branch already exists (local or remote)
    branch_exists = False
    local_result = run_command(["git", "rev-parse", "--verify", branch], cwd=root, check=False)
    if local_result.returncode == 0:
        branch_exists = True
        logger.debug(f"Branch {branch} exists locally")
    else:
        # Check remote
        remote_result = run_command(
            ["git", "rev-parse", "--verify", f"origin/{branch}"],
            cwd=root,
            check=False
        )
        if remote_result.returncode == 0:
            branch_exists = True
            logger.debug(f"Branch {branch} exists on remote")
        else:
            logger.debug(f"Branch {branch} does not exist locally or remotely")

    # Create worktree
    logger.info(f"Creating worktree for {wo_id}...")
    logger.info(f"  Base branch: {default_branch}")
    logger.info(f"  Worktree path: {worktree_path}")

    if branch_exists:
        logger.info(f"  Branch {branch} already exists, using it")
        run_command(
            ["git", "worktree", "add", str(worktree_path), branch],
            cwd=root
        )
    else:
        logger.info(f"  Creating new branch {branch} from {default_branch}")
        run_command(
            ["git", "worktree", "add", "-b", branch, str(worktree_path), default_branch],
            cwd=root
        )

    logger.info(f"✓ Worktree created: {worktree_path}")
    return branch, worktree_path


def cleanup_worktree(root: Path, wo_id: str) -> bool:
    """
    Remove a worktree for the given work order.

    Args:
        root: Repository root path
        wo_id: Work order ID (e.g., "WO-0012")

    Returns:
        True if successful, False otherwise
    """
    worktree_path = get_worktree_path(wo_id, root)
    branch = get_branch_name(wo_id)

    try:
        # Remove worktree
        if worktree_path.exists():
            logger.info(f"Removing worktree: {worktree_path}")
            run_command(["git", "worktree", "remove", str(worktree_path)], cwd=root)

        # Prune stale worktree references
        run_command(["git", "worktree", "prune"], cwd=root)

        # Optionally remove the branch
        try:
            run_command(["git", "branch", "-D", branch], cwd=root, check=False)
            logger.info(f"Removed branch: {branch}")
        except Exception:
            logger.info(f"Branch {branch} not removed (may not exist)")

        return True
    except Exception as e:
        logger.error(f"Failed to cleanup worktree: {e}")
        return False


def list_worktrees(root: Path) -> list[dict]:
    """
    List all git worktrees.

    Args:
        root: Repository root path

    Returns:
        List of dicts with worktree info
    """
    result = run_command(["git", "worktree", "list", "--porcelain"], cwd=root)

    worktrees = []
    current = {}
    for line in result.stdout.splitlines():
        if not line:
            if current:
                worktrees.append(current)
                current = {}
            continue

        key, value = line.split(" ", 1) if " " in line else (line, "")
        current[key] = value

    if current:
        worktrees.append(current)

    return worktrees


def create_lock(lock_path: Path, wo_id: str) -> bool:
    """
    Create an atomic lock file for a work order.

    Uses temp-rename pattern for atomicity on filesystems that support hard links.

    Args:
        lock_path: Path to lock file
        wo_id: Work order ID

    Returns:
        True if lock acquired, False otherwise
    """
    import tempfile

    if lock_path.exists():
        logger.warning(f"Lock already exists: {lock_path}")
        return False

    # Create temp file with unique name
    temp_fd, temp_path = tempfile.mkstemp(
        prefix=f"{wo_id}.",
        suffix=".lock",
        dir=lock_path.parent
    )
    os.close(temp_fd)

    try:
        # Write lock metadata
        with open(temp_path, "w") as f:
            f.write(f"Locked by ctx_wo_take.py at {datetime.now(timezone.utc).isoformat()}\n")
            f.write(f"PID: {os.getpid()}\n")
            f.write(f"User: {getpass.getuser()}\n")
            f.write(f"Hostname: {os.uname().nodename}\n")

        # Try atomic rename/link
        try:
            os.link(temp_path, lock_path)
            os.unlink(temp_path)
            logger.info(f"✓ Atomic lock acquired: {lock_path}")
            return True
        except OSError:
            # Fallback to rename if hard links not supported
            try:
                os.rename(temp_path, lock_path)
                logger.info(f"✓ Lock acquired (rename): {lock_path}")
                return True
            except OSError:
                os.unlink(temp_path)
                logger.warning(f"Failed to acquire lock: {lock_path}")
                return False
    except Exception as e:
        logger.error(f"Error creating lock: {e}")
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        return False


def check_lock_age(lock_path: Path, max_age_seconds: int = 3600) -> bool:
    """
    Check if a lock is stale (older than max_age_seconds).

    Args:
        lock_path: Path to lock file
        max_age_seconds: Maximum age in seconds (default: 3600 = 1 hour)

    Returns:
        True if lock is stale, False if active or doesn't exist
    """
    if not lock_path.exists():
        return False

    import time
    age = time.time() - lock_path.stat().st_mtime
    return age >= max_age_seconds


def update_lock_heartbeat(lock_path: Path) -> bool:
    """
    Update lock file timestamp to prevent stale detection.

    Args:
        lock_path: Path to lock file

    Returns:
        True if heartbeat updated, False otherwise
    """
    import tempfile

    if not lock_path.exists():
        logger.warning(f"Lock file not found for heartbeat: {lock_path}")
        return False

    try:
        content = lock_path.read_text()
        lines = content.split('\n')

        # Update timestamp line and add heartbeat
        updated_lines = []
        for line in lines:
            if line.startswith("Locked by ctx_wo_take.py at"):
                updated_lines.append(f"Locked by ctx_wo_take.py at {datetime.now(timezone.utc).isoformat()}")
                updated_lines.append(f"Heartbeat updated at: {datetime.now(timezone.utc).isoformat()}")
            elif not line.startswith("Heartbeat updated at:"):
                updated_lines.append(line)

        # Atomic write
        temp_fd, temp_path = tempfile.mkstemp(
            prefix=f"{lock_path.stem}.",
            suffix=".lock",
            dir=lock_path.parent
        )
        os.close(temp_fd)

        try:
            with open(temp_path, "w") as f:
                f.write('\n'.join(updated_lines))
            os.replace(temp_path, lock_path)
            logger.debug(f"Heartbeat updated: {lock_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to update heartbeat: {e}")
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            return False
    except Exception as e:
        logger.error(f"Error updating heartbeat: {e}")
        return False


def check_lock_validity(lock_path: Path, max_age_seconds: int = 3600) -> tuple[bool, Optional[dict]]:
    """
    Check if lock is valid (exists, not stale, process alive).

    **LIMITATIONS:**
    - TOCTOU vulnerability: Time gap between exists() check and read()
    - PID recycling: Possible (unlikely) PID reuse after lock creation
    - macOS-only: os.kill(pid, 0) behavior differs on Windows

    **MITIGATIONS:**
    - Fail-closed design: Returns False by default, True only when ALL checks pass
    - Short lock TTL (1 hour) reduces PID recycling window
    - Process existence check adds validation beyond timestamp

    Returns:
        Tuple of (is_valid, metadata_dict)
    """
    if not lock_path.exists():
        return False, None

    # Check age
    if check_lock_age(lock_path, max_age_seconds):
        logger.info(f"Lock is stale (> {max_age_seconds}s): {lock_path}")
        return False, None

    # Parse metadata and check if process is alive
    try:
        content = lock_path.read_text()
        metadata = {}
        for line in content.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip()] = value.strip()

        pid_str = metadata.get("PID")
        if pid_str:
            try:
                pid = int(pid_str)
                try:
                    os.kill(pid, 0)  # Signal 0 checks if process exists (macOS/BSD)
                    return True, metadata
                except OSError:
                    return False, metadata
            except ValueError as e:
                logger.warning(f"Invalid PID in lock: {pid_str} - {e}")
                return False, metadata

        # No PID found - consider invalid
        return False, metadata
    except (OSError, ValueError) as e:
        logger.error(f"Error parsing lock metadata: {type(e).__name__}: {e}")
        return False, None
    except Exception as e:
        logger.error(f"Unexpected error reading lock: {type(e).__name__}: {e}")
        return False, None


def execute_rollback(transaction, root: Path) -> tuple[bool, list[str]]:
    """
    Execute rollback for a failed transaction using BEST-EFFORT strategy.

    **BEST-EFFORT ROLLBACK:**
    Continues attempting rollback even if individual operations fail.
    This maximizes cleanup but may leave partial state.

    Args:
        transaction: Transaction with operations to rollback
        root: Repository root path

    Returns:
        Tuple of (all_succeeded, failed_operations)
        - all_succeeded: True only if ALL rollbacks succeeded
        - failed_operations: List of operation names that failed
    """
    if transaction.is_committed:
        logger.warning("Transaction already committed, no rollback needed")
        return True, []

    logger.info(f"Executing BEST-EFFORT rollback for WO {transaction.wo_id}")
    failed_ops = []

    # Execute rollbacks in reverse order (LIFO)
    for op in reversed(transaction.operations):
        logger.info(f"Rolling back: {op.name} - {op.description}")

        try:
            if op.rollback_type == "remove_lock":
                lock_path = root / "_ctx" / "jobs" / "running" / f"{transaction.wo_id}.lock"
                if lock_path.exists():
                    lock_path.unlink()
                    logger.info(f"✓ Removed lock: {lock_path}")

            elif op.rollback_type == "move_wo_to_pending":
                running_path = root / "_ctx" / "jobs" / "running" / f"{transaction.wo_id}.yaml"
                pending_path = root / "_ctx" / "jobs" / "pending" / f"{transaction.wo_id}.yaml"

                if running_path.exists():
                    wo_data = yaml.safe_load(running_path.read_text())
                    wo_data["status"] = "pending"
                    wo_data["started_at"] = None
                    wo_data["owner"] = None

                    pending_path.write_text(yaml.safe_dump(wo_data, sort_keys=False))
                    running_path.unlink()
                    logger.info(f"✓ Moved WO back to pending: {transaction.wo_id}")

            elif op.rollback_type == "remove_worktree":
                worktree_path = root / ".worktrees" / transaction.wo_id
                if worktree_path.exists():
                    cleanup_worktree(root, transaction.wo_id)
                    logger.info(f"✓ Removed worktree: {worktree_path}")

            elif op.rollback_type == "remove_branch":
                branch = get_branch_name(transaction.wo_id)
                run_command(["git", "branch", "-D", branch], cwd=root, check=False)
                logger.info(f"✓ Removed branch: {branch}")

        except Exception as e:
            error_msg = f"{op.name}: {type(e).__name__}: {e}"
            logger.error(f"✗ Rollback failed: {error_msg}")
            failed_ops.append(error_msg)
            # CONTINUE anyway - best-effort cleanup

    # Report final status
    if failed_ops:
        logger.warning(f"Rollback completed with {len(failed_ops)} failures: {failed_ops}")
        logger.warning(f"Manual intervention may be required for WO {transaction.wo_id}")
        return False, failed_ops
    else:
        logger.info(f"✓ Rollback completed successfully for WO {transaction.wo_id}")
        return True, []
