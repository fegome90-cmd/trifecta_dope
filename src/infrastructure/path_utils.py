"""Path Guardrails - Security boundary for path validation.

This module provides security-critical path validation functions:
- Canonicalization: Convert to absolute, resolved paths
- Traversal prevention: Block ../ escapes outside root
- Scope validation: Ensure paths are within expected boundaries

IMPORTANT: These functions are security boundaries. Do not weaken validation.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Union


class PathTraversalError(ValueError):
    """Raised when a path escapes intended root."""

    def __init__(self, candidate: Path, root: Path) -> None:
        self.candidate = candidate
        self.root = root
        super().__init__(f"Path '{candidate}' escapes root '{root}'")


class InvalidSegmentError(ValueError):
    """Raised when segment validation fails."""

    def __init__(self, path: Path, reason: str) -> None:
        self.path = path
        self.reason = reason
        super().__init__(f"Invalid segment '{path}': {reason}")


def canonicalize_path(input_path: Union[str, Path]) -> Path:
    """Canonicalize a path to absolute, resolved form.

    Steps:
    1. Convert to Path object
    2. Expand user home (~)
    3. Resolve to real path (follows symlinks, resolves . and ..)

    Args:
        input_path: Path string or Path object

    Returns:
        Absolute, resolved Path object

    Raises:
        ValueError: If path cannot be canonicalized
    """
    if not input_path:
        raise ValueError("Empty path provided")

    path = Path(input_path)

    # Step 1: Expand user home
    try:
        path = path.expanduser()
    except (OSError, RuntimeError) as e:
        raise ValueError(f"Cannot expand user in path: {input_path}") from e

    # Step 2: Resolve to absolute path (follows symlinks)
    try:
        path = path.resolve()
    except (OSError, RuntimeError) as e:
        raise ValueError(f"Cannot resolve path: {input_path}") from e

    return path


def ensure_within_root(candidate: Union[str, Path], root: Union[str, Path]) -> Path:
    """Ensure candidate path is contained within root.

    SECURITY: This uses relative_to() which is secure against traversal.
    Do NOT use startswith() - it is insecure.

    Args:
        candidate: Path to validate
        root: Root path that candidate must be within

    Returns:
        Canonicalized candidate path if valid

    Raises:
        PathTraversalError: If candidate escapes root
    """
    # Canonicalize both paths
    candidate = canonicalize_path(candidate)
    root = canonicalize_path(root)

    # Check containment using relative_to() - raises if escape detected
    try:
        candidate.relative_to(root)
    except ValueError:
        raise PathTraversalError(candidate, root)

    return candidate


def validate_segment_exists(segment: Union[str, Path]) -> Path:
    """Validate segment path exists and is accessible.

    Args:
        segment: Segment path to validate

    Returns:
        Canonicalized path if valid

    Raises:
        InvalidSegmentError: If segment doesn't exist or is inaccessible
    """
    segment = canonicalize_path(segment)

    if not segment.exists():
        raise InvalidSegmentError(segment, "path does not exist")

    if not os.access(segment, os.R_OK):
        raise InvalidSegmentError(segment, "path not readable")

    return segment


def validate_segment_is_git_repo(segment: Union[str, Path]) -> Path:
    """Validate segment is a git repository.

    Args:
        segment: Segment path to validate

    Returns:
        Canonicalized path if valid

    Raises:
        InvalidSegmentError: If segment is not a git repository
    """
    segment = validate_segment_exists(segment)

    git_dir = segment / ".git"
    if not git_dir.exists():
        # Also check for .git file (git worktree)
        git_file = segment / ".git"
        if not git_file.exists():
            raise InvalidSegmentError(segment, "not a git repository (no .git)")

    return segment


def validate_segment_has_ctx(segment: Union[str, Path]) -> Path:
    """Validate segment contains _ctx directory.

    This is the Trifecta segment marker.

    Args:
        segment: Segment path to validate

    Returns:
        Canonicalized path if valid

    Raises:
        InvalidSegmentError: If segment lacks _ctx
    """
    segment = validate_segment_exists(segment)

    ctx_dir = segment / "_ctx"
    if not ctx_dir.exists():
        raise InvalidSegmentError(segment, "not a Trifecta segment (no _ctx)")

    return segment


def validate_segment(
    segment: Union[str, Path],
    require_git: bool = False,
    require_ctx: bool = False,
) -> Path:
    """Comprehensive segment validation.

    Args:
        segment: Segment path to validate
        require_git: If True, segment must be a git repository
        require_ctx: If True, segment must contain _ctx directory

    Returns:
        Canonicalized path if all validations pass

    Raises:
        InvalidSegmentError: If any validation fails
    """
    segment = canonicalize_path(segment)

    # First check it exists
    segment = validate_segment_exists(segment)

    # Apply additional validations
    if require_git:
        segment = validate_segment_is_git_repo(segment)

    if require_ctx:
        segment = validate_segment_has_ctx(segment)

    return segment


def validate_wo_id(wo_id: str) -> str:
    """Validate Work Order ID format.

    Pattern: WO-\d{4}

    Args:
        wo_id: Work Order ID string

    Returns:
        Validated WO ID

    Raises:
        ValueError: If WO ID format is invalid
    """
    if not wo_id:
        raise ValueError("Empty WO ID")

    import re

    pattern = r"^WO-\d{4}$"

    if not re.match(pattern, wo_id):
        raise ValueError(f"Invalid WO ID '{wo_id}': must match pattern WO-XXXX (e.g., WO-0053)")

    return wo_id
