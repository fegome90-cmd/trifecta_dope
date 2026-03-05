"""
Skill metadata contracts for Trifecta skill system.

Pure domain module - no external dependencies.
Uses dataclasses and Result pattern for validation.

Author: Trifecta Team
Date: 2026-03-05
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from src.domain.result import Ok, Err, Result


# Valid input types for skill inputs
InputType = Literal["string", "file", "json", "boolean", "number"]


@dataclass(frozen=True)
class SkillValidationError:
    """A single validation error for skill metadata."""

    field: str
    message: str
    value: object | None = None

    def __str__(self) -> str:
        if self.value is not None:
            return f"{self.field}: {self.message} (got: {self.value!r})"
        return f"{self.field}: {self.message}"


@dataclass(frozen=True)
class SkillInput:
    """An input parameter for a skill."""

    name: str
    type: str  # Validated by validate_skill_input, not here (no exceptions in dataclass)
    required: bool = True
    description: str = ""


def validate_skill_input(inp: SkillInput) -> Result[SkillInput, list[SkillValidationError]]:
    """Validate a single skill input."""
    errors: list[SkillValidationError] = []

    if not inp.name or not inp.name.strip():
        errors.append(SkillValidationError("input.name", "name cannot be empty"))

    valid_types: tuple[str, ...] = ("string", "file", "json", "boolean", "number")
    if inp.type not in valid_types:
        errors.append(
            SkillValidationError("input.type", f"type must be one of {valid_types}", inp.type)
        )

    if errors:
        return Err(errors)
    return Ok(inp)


@dataclass(frozen=True)
class SkillMeta:
    """
    Metadata for a skill.

    Designed to be extracted from SKILL.md frontmatter YAML.
    All fields have defaults to allow incremental migration.
    """

    name: str
    description: str
    requires: list[str] = field(default_factory=list)
    inputs: list[SkillInput] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    levels: list[str] = field(default_factory=list)  # Optional: L0, L1, L2 detail levels
    source_path: str = ""  # Path to SKILL.md (for error reporting)


def validate_skill_meta(meta: SkillMeta) -> Result[SkillMeta, list[SkillValidationError]]:
    """
    Validate skill metadata.

    Returns:
        Ok(SkillMeta) if valid
        Err(list[SkillValidationError]) if invalid

    Validation rules:
        - name: non-empty string
        - description: non-empty string
        - requires: list of strings (can be empty)
        - inputs: list of valid SkillInput objects
        - outputs: list of strings (can be empty)
    """
    errors: list[SkillValidationError] = []

    # Validate name
    if not meta.name or not meta.name.strip():
        errors.append(SkillValidationError("name", "name cannot be empty"))

    # Validate description
    if not meta.description or not meta.description.strip():
        errors.append(SkillValidationError("description", "description cannot be empty"))

    # Validate requires (must be list of strings)
    for i, req in enumerate(meta.requires):
        if not isinstance(req, str):
            errors.append(
                SkillValidationError(f"requires[{i}]", "must be a string", req)
            )

    # Validate outputs (must be list of strings)
    for i, out in enumerate(meta.outputs):
        if not isinstance(out, str):
            errors.append(
                SkillValidationError(f"outputs[{i}]", "must be a string", out)
            )

    # Validate levels (must be list of strings if present)
    for i, level in enumerate(meta.levels):
        if not isinstance(level, str):
            errors.append(
                SkillValidationError(f"levels[{i}]", "must be a string", level)
            )

    # Validate inputs (must be valid SkillInput objects)
    for i, inp in enumerate(meta.inputs):
        inp_result = validate_skill_input(inp)
        if inp_result.is_err():
            for inp_err in inp_result.unwrap_err():
                # Prefix with input index
                errors.append(
                    SkillValidationError(
                        f"inputs[{i}].{inp_err.field}",
                        inp_err.message,
                        inp_err.value,
                    )
                )

    if errors:
        return Err(errors)

    return Ok(meta)


# Alias for backward compatibility
SkillError = SkillValidationError
