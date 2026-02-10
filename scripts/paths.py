"""Centralized path constants and utilities for WO system.

This module provides a single source of truth for all filesystem paths
used by the Work Order system. Changes to directory structure should be
made here to propagate across all scripts.

Usage:
    from scripts.paths import (
        get_lock_path,
        get_wo_pending_path,
        get_worktree_path,
        repo_root,
        WORKTREE_BASE,
        RUNNING_DIR,
    )

    lock_file = get_lock_path(repo_root(), "WO-0001")
    worktree = get_worktree_path(repo_root(), "WO-0001")
"""

from dataclasses import dataclass
from pathlib import Path


# =============================================================================
# Directory Constants
# =============================================================================

_CTX_DIR = Path("_ctx")
# Worktrees are created OUTSIDE the repo as siblings (e.g., ../.worktrees/WO-XXXX)
# This follows Git conventions and is compatible with tools like Sidecar
_WORKTREES_DIR = Path(".worktrees")  # Relative to parent directory

# Job state directories
_JOBS_BASE = _CTX_DIR / "jobs"
_PENDING_DIR = _JOBS_BASE / "pending"
_RUNNING_DIR = _JOBS_BASE / "running"
_DONE_DIR = _JOBS_BASE / "done"
_FAILED_DIR = _JOBS_BASE / "failed"

# Exported constants for backward compatibility
WORKTREE_BASE = _WORKTREES_DIR
PENDING_DIR = _PENDING_DIR
RUNNING_DIR = _RUNNING_DIR
DONE_DIR = _DONE_DIR
FAILED_DIR = _FAILED_DIR


# =============================================================================
# Path Builder Functions
# =============================================================================


def get_lock_path(root: Path, wo_id: str) -> Path:
    """Get the path to a WO's lock file.

    Args:
        root: Repository root directory
        wo_id: Work Order ID (e.g., "WO-0001")

    Returns:
        Path to the lock file in _ctx/jobs/running/
    """
    return root / _RUNNING_DIR / f"{wo_id}.lock"


def get_wo_pending_path(root: Path, wo_id: str) -> Path:
    """Get the path to a WO's YAML file in pending state.

    Args:
        root: Repository root directory
        wo_id: Work Order ID (e.g., "WO-0001")

    Returns:
        Path to the WO file in _ctx/jobs/pending/
    """
    return root / _PENDING_DIR / f"{wo_id}.yaml"


def get_wo_running_path(root: Path, wo_id: str) -> Path:
    """Get the path to a WO's YAML file in running state.

    Args:
        root: Repository root directory
        wo_id: Work Order ID (e.g., "WO-0001")

    Returns:
        Path to the WO file in _ctx/jobs/running/
    """
    return root / _RUNNING_DIR / f"{wo_id}.yaml"


def get_wo_done_path(root: Path, wo_id: str) -> Path:
    """Get the path to a WO's YAML file in done state.

    Args:
        root: Repository root directory
        wo_id: Work Order ID (e.g., "WO-0001")

    Returns:
        Path to the WO file in _ctx/jobs/done/
    """
    return root / _DONE_DIR / f"{wo_id}.yaml"


def get_wo_failed_path(root: Path, wo_id: str) -> Path:
    """Get the path to a WO's YAML file in failed state.

    Args:
        root: Repository root directory
        wo_id: Work Order ID (e.g., "WO-0001")

    Returns:
        Path to the WO file in _ctx/jobs/failed/
    """
    return root / _FAILED_DIR / f"{wo_id}.yaml"


def get_worktree_path(root: Path, wo_id: str) -> Path:
    """Get the path to a WO's worktree directory.

    Worktrees are created OUTSIDE the repository as sibling directories.
    This follows Git conventions and ensures compatibility with tools
    like Sidecar that expect worktrees to be outside the main worktree.

    Args:
        root: Repository root directory
        wo_id: Work Order ID (e.g., "WO-0001")

    Returns:
        Path to the worktree in ../.worktrees/ (sibling of repo)

    Example:
        >>> repo_root = Path("/dev/trifecta_dope")
        >>> get_worktree_path(repo_root, "WO-0001")
        Path("/dev/.worktrees/WO-0001")
    """
    # Use root.parent to place worktrees outside the repo
    return root.parent / _WORKTREES_DIR / wo_id


def get_branch_name(wo_id: str) -> str:
    """Get the git branch name for a WO.

    Args:
        wo_id: Work Order ID (e.g., "WO-0001")

    Returns:
        Branch name in format: feat/wo-WO-XXXX
    """
    return f"feat/wo-{wo_id}"


def repo_root() -> Path:
    """Find repository root by searching for pyproject.toml upwards.

    Returns:
        Path to repository root directory.

    Raises:
        FileNotFoundError: If pyproject.toml not found within 5 levels.
    """
    current = Path(__file__).resolve().parent
    for _ in range(5):
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Repository root not found (pyproject.toml missing)")


# =============================================================================
# Path Validation
# =============================================================================


@dataclass(frozen=True)
class PathValidationResult:
    """Result of path validation."""

    is_valid: bool
    error_message: str | None = None
    missing_paths: tuple[Path, ...] = ()

    @staticmethod
    def valid() -> "PathValidationResult":
        return PathValidationResult(is_valid=True)

    @staticmethod
    def invalid(error: str, *missing: Path) -> "PathValidationResult":
        return PathValidationResult(is_valid=False, error_message=error, missing_paths=missing)


def validate_wo_paths(root: Path, wo_id: str) -> PathValidationResult:
    """Validate that all required WO directories exist.

    Args:
        root: Repository root directory
        wo_id: Work Order ID (for error messages)

    Returns:
        PathValidationResult indicating if paths are valid
    """
    missing: list[Path] = []

    # Check that jobs base exists
    if not (root / _JOBS_BASE).exists():
        missing.append(root / _JOBS_BASE)

    # Check that all state directories exist
    for state_dir in [_PENDING_DIR, _RUNNING_DIR, _DONE_DIR, _FAILED_DIR]:
        full_path = root / state_dir
        if not full_path.exists():
            missing.append(full_path)

    if missing:
        return PathValidationResult.invalid(
            f"Required WO directories missing for {wo_id}", *missing
        )

    return PathValidationResult.valid()


def ensure_wo_directories(root: Path) -> tuple[Path, ...]:
    """Ensure all required WO directories exist, creating them if needed.

    Args:
        root: Repository root directory

    Returns:
        Tuple of created directories (empty if all existed)
    """
    created: list[Path] = []

    directories = [
        root / _JOBS_BASE,
        root / _PENDING_DIR,
        root / _RUNNING_DIR,
        root / _DONE_DIR,
        root / _FAILED_DIR,
    ]

    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created.append(directory)

    return tuple(created)
