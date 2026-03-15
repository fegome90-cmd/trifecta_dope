"""
Application layer: Skill linting use case.

Orchestrates skill discovery and validation.

Author: Trifecta Team
Date: 2026-03-05
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.domain.skill_contracts import SkillValidationError, validate_skill_meta
from src.infrastructure.skills_fs import discover_skills_from_paths


@dataclass(frozen=True)
class SkillLintResult:
    """Result of linting a single skill."""

    path: str
    name: str
    valid: bool
    errors: list[SkillValidationError]

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "name": self.name,
            "valid": self.valid,
            "errors": [str(e) for e in self.errors],
        }


@dataclass(frozen=True)
class SkillLintReport:
    """Full lint report for all skills."""

    skills: list[SkillLintResult]
    total: int
    valid_count: int
    invalid_count: int

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "valid": self.valid_count,
            "invalid": self.invalid_count,
            "skills": [s.to_dict() for s in self.skills],
        }


def lint_skills(
    paths: list[Path],
) -> SkillLintReport:
    """
    Lint all skills in the given paths.

    Args:
        paths: List of directories or SKILL.md files to lint

    Returns:
        SkillLintReport with results for each skill
    """
    discovered = discover_skills_from_paths(paths)
    results: list[SkillLintResult] = []

    for skill in discovered:
        validation = validate_skill_meta(skill.meta)
        if validation.is_ok():
            results.append(
                SkillLintResult(
                    path=str(skill.path),
                    name=skill.meta.name or "(unnamed)",
                    valid=True,
                    errors=[],
                )
            )
        else:
            errors = validation.unwrap_err() or []
            results.append(
                SkillLintResult(
                    path=str(skill.path),
                    name=skill.meta.name or "(unnamed)",
                    valid=False,
                    errors=errors,
                )
            )

    valid_count = sum(1 for r in results if r.valid)
    invalid_count = len(results) - valid_count

    return SkillLintReport(
        skills=results,
        total=len(results),
        valid_count=valid_count,
        invalid_count=invalid_count,
    )
