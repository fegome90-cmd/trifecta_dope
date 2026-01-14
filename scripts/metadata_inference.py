#!/usr/bin/env python3
"""
Metadata inference utilities for Work Order repair.

This module provides functions to infer missing WO metadata from the actual
system state (lock files, git worktrees, etc.) for repair operations.
"""
import getpass
import logging
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from scripts.paths import (
    get_lock_path,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Result Types
# =============================================================================

@dataclass(frozen=True)
class InferenceResult:
    """Result of metadata inference."""
    success: bool
    inferred: dict
    errors: list[str]
    warnings: list[str]

    @staticmethod
    def success_with(inferred: dict) -> "InferenceResult":
        return InferenceResult(success=True, inferred=inferred, errors=[], warnings=[])

    @staticmethod
    def failure(errors: list[str], warnings: list[str] | None = None) -> "InferenceResult":
        return InferenceResult(
            success=False,
            inferred={},
            errors=errors,
            warnings=warnings or []
        )


# =============================================================================
# Lock File Parsing
# =============================================================================

def parse_lock_file(lock_path: Path) -> dict:
    """
    Parse lock file to extract metadata.

    Args:
        lock_path: Path to lock file

    Returns:
        Dictionary with lock metadata

    Raises:
        FileNotFoundError: Lock file doesn't exist
        UnicodeDecodeError: Lock file has invalid encoding
        ValueError: Lock file is malformed
    """
    try:
        content = lock_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise
    except UnicodeDecodeError:
        logger.error(f"Lock file encoding error: {lock_path} [WO-TAKE-003]")
        raise

    metadata = {}
    for line in content.splitlines():
        if "Locked by ctx_wo_take.py at" in line:
            # Extract timestamp
            match = re.search(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", line)
            if match:
                metadata["locked_at"] = match.group(1)
        elif "PID:" in line:
            metadata["pid"] = int(line.split("PID:")[1].strip())
        elif "User:" in line:
            metadata["user"] = line.split("User:")[1].strip()
        elif "Hostname:" in line:
            metadata["hostname"] = line.split("Hostname:")[1].strip()

    return metadata


def is_lock_stale(lock_path: Path, max_age_seconds: int = 3600) -> bool:
    """
    Check if lock file is stale (older than max_age_seconds).

    Args:
        lock_path: Path to lock file
        max_age_seconds: Maximum age in seconds (default: 3600 = 1 hour)

    Returns:
        True if lock is stale or doesn't exist
    """
    if not lock_path.exists():
        return True

    try:
        mtime = lock_path.stat().st_mtime
        age = (datetime.now(timezone.utc).timestamp() - mtime)
        return age >= max_age_seconds
    except OSError:
        return True


def is_lock_process_alive(lock_path: Path) -> bool:
    """
    Check if the process that created the lock is still alive.

    Args:
        lock_path: Path to lock file

    Returns:
        True if process is alive, False otherwise
    """
    try:
        metadata = parse_lock_file(lock_path)
        pid = metadata.get("pid")
        if pid is None:
            return False

        # Check if process exists
        try:
            os.kill(pid, 0)  # Signal 0 doesn't kill, just checks existence
            return True
        except OSError:
            return False
    except (FileNotFoundError, ValueError, UnicodeDecodeError):
        return False


def check_lock_validity(
    lock_path: Path,
    max_age_seconds: int = 3600
) -> tuple[bool, Optional[dict]]:
    """
    Check if lock file is valid (exists, not stale, process alive).

    Args:
        lock_path: Path to lock file
        max_age_seconds: Maximum age in seconds (default: 3600)

    Returns:
        Tuple of (is_valid, metadata_dict)
    """
    if not lock_path.exists():
        return False, None

    if is_lock_stale(lock_path, max_age_seconds):
        return False, None

    if not is_lock_process_alive(lock_path):
        return False, None

    try:
        metadata = parse_lock_file(lock_path)
        return True, metadata
    except (FileNotFoundError, ValueError, UnicodeDecodeError):
        return False, None


# =============================================================================
# Git Worktree Operations
# =============================================================================

def get_worktrees_from_git(root: Path) -> dict[str, dict]:
    """
    Parse `git worktree list` output to get all worktrees.

    Args:
        root: Repository root directory

    Returns:
        Dictionary mapping wo_id to worktree metadata:
        {
            "WO-0018B": {
                "path": ".worktrees/WO-0018B",
                "branch": "feat/wo-WO-0018B",
                "commit": "abc123"
            }
        }
    """
    result = {}
    try:
        output = subprocess.check_output(
            ["git", "worktree", "list"],
            cwd=root,
            text=True,
            stderr=subprocess.DEVNULL
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.error(f"Failed to get worktree list: {e} [WO-TAKE-004]")
        return result

    for line in output.splitlines():
        if not line.strip():
            continue

        parts = line.split()
        if len(parts) < 3:
            continue

        worktree_path = parts[0]
        # Extract branch from [branch] or (branch)
        branch_match = re.search(r"\[([^\]]+)\]", line)
        if branch_match:
            branch = branch_match.group(1)
        else:
            branch = None

        # Extract WO ID from path
        wo_match = re.search(r"\.worktrees/(WO-\d{4}[A-Z]?)", worktree_path)
        if wo_match:
            wo_id = wo_match.group(1)
            result[wo_id] = {
                "path": worktree_path,
                "branch": branch,
                "commit": parts[1] if len(parts) > 1 else None
            }

    return result


# =============================================================================
# Metadata Inference
# =============================================================================

def infer_metadata_from_system(
    wo_id: str,
    root: Path,
    required_fields: set[str]
) -> InferenceResult:
    """
    Infer missing WO metadata from system state.

    Args:
        wo_id: Work Order ID
        root: Repository root
        required_fields: Set of fields that are missing

    Returns:
        InferenceResult with inferred metadata
    """
    inferred = {}
    errors = []
    warnings = []

    # Infer status
    if "status" in required_fields:
        inferred["status"] = "running"

    # Infer owner from lock file
    if "owner" in required_fields:
        lock_path = get_lock_path(root, wo_id)
        try:
            is_valid, lock_metadata = check_lock_validity(lock_path)
            if is_valid and lock_metadata:
                inferred["owner"] = lock_metadata.get("user", getpass.getuser())
            else:
                errors.append("Lock file missing, stale, or process dead")
        except Exception as e:
            errors.append(f"Failed to read lock: {str(e)}")

    # Infer started_at from lock file
    if "started_at" in required_fields:
        lock_path = get_lock_path(root, wo_id)
        try:
            metadata = parse_lock_file(lock_path)
            if "locked_at" in metadata:
                inferred["started_at"] = metadata["locked_at"]
            else:
                # Use lock file mtime
                mtime = datetime.fromtimestamp(
                    lock_path.stat().st_mtime,  # st_mtime is property, not method
                    tz=timezone.utc
                )
                inferred["started_at"] = mtime.isoformat()
        except Exception:
            # Fallback to current time
            inferred["started_at"] = datetime.now(timezone.utc).isoformat()
            warnings.append("Using current time for started_at (lock mtime unavailable)")

    # Infer branch and worktree from git
    if "branch" in required_fields or "worktree" in required_fields:
        worktrees = get_worktrees_from_git(root)

        if wo_id in worktrees:
            wt_info = worktrees[wo_id]
            if "branch" in required_fields:
                inferred["branch"] = wt_info["branch"]
            if "worktree" in required_fields:
                # Make relative to root
                wt_path = Path(wt_info["path"])
                try:
                    inferred["worktree"] = str(wt_path.relative_to(root))
                except ValueError:
                    inferred["worktree"] = wt_info["path"]
        else:
            errors.append("Worktree not found in git worktree list")

    # Determine success
    if errors:
        return InferenceResult.failure(errors, warnings)
    else:
        return InferenceResult.success_with(inferred)


# =============================================================================
# Verification
# =============================================================================

def verify_metadata_completeness(wo_data: dict) -> list[str]:
    """
    Check if WO data has all required metadata fields.

    Args:
        wo_data: WO data dictionary

    Returns:
        List of missing required fields (empty if complete)
    """
    required = {"status", "owner", "branch", "worktree", "started_at"}
    missing = [field for field in required if not wo_data.get(field)]
    return missing


def validate_inferred_metadata(
    wo_id: str,
    wo_data: dict,
    root: Path
) -> tuple[bool, list[str]]:
    """
    Validate that inferred metadata is consistent with system state.

    Args:
        wo_id: Work Order ID
        wo_data: WO data with inferred metadata
        root: Repository root

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []

    # Verify worktree exists
    worktree_path = root / (wo_data.get("worktree", ""))
    if not worktree_path.exists():
        errors.append(f"Worktree path doesn't exist: {worktree_path}")

    # Verify lock exists
    lock_path = get_lock_path(root, wo_id)
    if not lock_path.exists():
        errors.append(f"Lock file doesn't exist: {lock_path}")

    # Verify branch matches worktree
    worktrees = get_worktrees_from_git(root)
    if wo_id in worktrees:
        expected_branch = worktrees[wo_id]["branch"]
        actual_branch = wo_data.get("branch")
        if actual_branch != expected_branch:
            errors.append(f"Branch mismatch: expected {expected_branch}, got {actual_branch}")

    return (len(errors) == 0, errors)
