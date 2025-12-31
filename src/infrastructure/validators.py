"""
Segment Validation Logic (Pure Core)

This module contains validation logic for Trifecta segments.
Follows Clean Architecture principles:
- Pure functions (no side effects)
- Immutable results (frozen dataclasses)
- Type-safe (mypy --strict compatible)

Extracted from scripts/install_FP.py as part of v1.1 refactoring.

Author: Trifecta Team
Date: 2025-12-30
Phase: GREEN (Implementation for TDD Red-Green-Refactor)
"""

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from src.domain.result import Err, Ok


@dataclass(frozen=True)
class ValidationResult:
    """
    Immutable result of segment structure validation.

    Attributes:
        valid: True if segment structure is valid, False otherwise
        errors: List of error messages (empty if valid=True)

    Examples:
        >>> result = ValidationResult(valid=True, errors=[])
        >>> result.valid
        True

        >>> result = ValidationResult(valid=False, errors=["Missing skill.md"])
        >>> result.errors
        ['Missing skill.md']
    """

    valid: bool
    errors: List[str]


def validate_segment_structure(path: Path) -> ValidationResult:
    """
    Validates that a segment directory follows the Trifecta structure.

    Strict 3+1 Contract:
        - skill.md (fixed filename)
        - _ctx/agent_<segment_id>.md
        - _ctx/prime_<segment_id>.md
        - _ctx/session_<segment_id>.md

    Where segment_id = normalize_segment_id(path.name)

    Legacy files (agent.md, prime.md, session.md) are ERRORS, not warnings.
    Ambiguity (0 or >1 matches) is an ERROR.

    Args:
        path: Path to the segment directory to validate

    Returns:
        ValidationResult with valid=True if structure is correct,
        or valid=False with list of errors

    Pure Function:
        - No side effects (no prints, no logging, no state mutations)
        - Deterministic (same input → same output)
        - Thread-safe
    """
    from src.domain.naming import normalize_segment_id

    errors: List[str] = []

    # Check 1: Path exists
    if not path.exists():
        return ValidationResult(False, [f"Path not found: {path}"])

    # Check 2: skill.md (fixed filename, always required)
    if not (path / "skill.md").exists():
        errors.append("Missing generic entry point: skill.md")

    # Check 3: _ctx directory exists
    ctx_dir = path / "_ctx"
    if not ctx_dir.exists():
        errors.append("Missing directory: _ctx/")
        # Early return: can't validate files inside non-existent directory
        return ValidationResult(False, errors)

    # Check 4: Normalize segment ID
    segment_id = normalize_segment_id(path.name)

    # Check 5: Exact 3+1 contract with normalized ID
    expected_files = [
        f"agent_{segment_id}.md",
        f"prime_{segment_id}.md",
        f"session_{segment_id}.md",
    ]

    for filename in expected_files:
        expected_path = ctx_dir / filename
        if not expected_path.exists():
            errors.append(f"Missing context file: _ctx/{filename}")

    # Check 6: Detect ambiguity (multiple agent_*.md, prime_*.md, session_*.md)
    for prefix in ["agent", "prime", "session"]:
        matches = list(ctx_dir.glob(f"{prefix}_*.md"))
        if len(matches) > 1:
            errors.append(
                f"Ambiguous: found {len(matches)} {prefix}_*.md files in _ctx/ "
                f"(expected exactly 1: {prefix}_{segment_id}.md)"
            )

    # Validation complete
    return ValidationResult(valid=len(errors) == 0, errors=errors)


def detect_legacy_context_files(path: Path) -> List[str]:
    """
    Detect legacy (non-dynamic) context filenames inside _ctx.
    Returns a list of legacy filenames that exist, in stable order.
    """
    legacy_names = ["agent.md", "prime.md", "session.md"]
    ctx_dir = path / "_ctx"
    if not ctx_dir.exists():
        return []
    return [name for name in legacy_names if (ctx_dir / name).exists()]


def validate_segment_fp(path: Path) -> "Ok[ValidationResult] | Err[List[str]]":
    """
    FP wrapper for validate_segment_structure.

    Returns Result monad instead of ValidationResult directly.
    This enables Railway Oriented Programming in the CLI.

    Args:
        path: Path to the segment directory to validate

    Returns:
        Ok(ValidationResult) if segment is valid
        Err(list[str]) with error messages if invalid

    Example:
        match validate_segment_fp(segment_path):
            case Ok(result):
                # proceed with valid segment
            case Err(errors):
                # handle validation errors
    """
    from src.domain.result import Err, Ok

    result = validate_segment_structure(path)

    if result.valid:
        return Ok(result)
    else:
        return Err(result.errors)


def validate_agents_constitution(path: Path) -> "Ok[ValidationResult] | Err[List[str]]":
    """
    Validates adherence to the AGENTS.md Constitution.

    Phase 1 Rules:
    1. AGENTS.md must exist in the segment root.
    2. AGENTS.md must not be empty.

    Args:
        path: Path to the segment directory (root)

    Returns:
        Ok(ValidationResult) if valid
        Err(list[str]) if Constitution is violated
    """
    from src.domain.result import Err, Ok

    agents_path = path / "AGENTS.md"

    if not agents_path.exists():
        return Err(["Failed Constitution: missing AGENTS.md in segment root"])

    try:
        content = agents_path.read_text().strip()
        if not content:
            return Err(["Failed Constitution: AGENTS.md is empty"])
    except Exception:
        # Deterministic error output (no dynamic exception details)
        return Err(["Failed Constitution: AGENTS.md cannot be read"])

    return Ok(ValidationResult(valid=True, errors=[]))
