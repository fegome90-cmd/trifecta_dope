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
from typing import List


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
    
    Dynamic Naming Convention:
        If segment folder is named 'marketing', expects:
        - skill.md (fixed filename)
        - _ctx/agent_marketing.md (dynamic: agent_{segment_name}.md)
        - _ctx/prime_marketing.md (dynamic: prime_{segment_name}.md)
        - _ctx/session_marketing.md (dynamic: session_{segment_name}.md)
    
    Args:
        path: Path to the segment directory to validate
    
    Returns:
        ValidationResult with valid=True if structure is correct,
        or valid=False with list of errors
    
    Pure Function:
        - No side effects (no prints, no logging, no state mutations)
        - Deterministic (same input → same output)
        - Thread-safe
    
    Examples:
        >>> from pathlib import Path
        >>> result = validate_segment_structure(Path("/path/to/segment"))
        >>> if result.valid:
        ...     print("Valid segment")
        ... else:
        ...     print(f"Errors: {result.errors}")
    """
    errors: List[str] = []
    
    # Check 1: Path exists
    if not path.exists():
        return ValidationResult(False, [f"Path not found: {path}"])

    # Extract segment name from directory name
    # This is used for dynamic naming validation
    context_name = path.name
    
    # Check 2: skill.md (fixed filename, always required)
    if not (path / "skill.md").exists():
        errors.append("Missing generic entry point: skill.md")
    
    # Check 3: _ctx directory exists
    ctx_dir = path / "_ctx"
    if not ctx_dir.exists():
        errors.append("Missing directory: _ctx/")
        # Early return: can't validate files inside non-existent directory
        return ValidationResult(False, errors)

    # Check 4: Dynamic named files (interpolate segment name)
    expected_files = [
        f"agent_{context_name}.md",
        f"prime_{context_name}.md",
        f"session_{context_name}.md"
    ]

    for filename in expected_files:
        expected_path = ctx_dir / filename
        if not expected_path.exists():
            errors.append(f"Missing context file: _ctx/{filename}")

    # Validation complete
    return ValidationResult(valid=len(errors) == 0, errors=errors)
