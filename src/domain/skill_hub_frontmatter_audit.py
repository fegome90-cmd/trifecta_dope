"""Audit malformed skill-hub frontmatter from a manifest-backed source set.

Pure domain module:
- no filesystem IO
- no subprocesses
- deterministic parsing/classification only
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal

import yaml

FrontmatterErrorFamily = Literal["missing_frontmatter", "unterminated_frontmatter", "yaml_parse_error"]


@dataclass(frozen=True)
class FrontmatterAuditTarget:
    """Single manifest-backed source candidate to audit."""

    source: str
    name: str
    source_path: str
    content: str


@dataclass(frozen=True)
class FrontmatterAuditFailure:
    """One malformed frontmatter finding."""

    source: str
    name: str
    source_path: str
    error_family: FrontmatterErrorFamily
    error_type: str
    error_message: str


@dataclass(frozen=True)
class FrontmatterAuditReport:
    """Deterministic audit report for a manifest-backed skill set."""

    total_targets: int
    failures: tuple[FrontmatterAuditFailure, ...]

    @property
    def broken_count(self) -> int:
        return len(self.failures)

    def count_by_error_type(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for failure in self.failures:
            counts[failure.error_type] = counts.get(failure.error_type, 0) + 1
        return counts


def audit_frontmatter_targets(targets: Iterable[FrontmatterAuditTarget]) -> FrontmatterAuditReport:
    """Audit a manifest-backed set of source contents for malformed frontmatter."""
    failures: list[FrontmatterAuditFailure] = []
    total_targets = 0
    for target in targets:
        total_targets += 1
        failure = inspect_frontmatter(target)
        if failure is not None:
            failures.append(failure)
    return FrontmatterAuditReport(total_targets=total_targets, failures=tuple(failures))


def inspect_frontmatter(target: FrontmatterAuditTarget) -> FrontmatterAuditFailure | None:
    """Return a failure when the target frontmatter is malformed, otherwise None."""
    lines = target.content.strip().split("\n")
    if not lines or lines[0].strip() != "---":
        return FrontmatterAuditFailure(
            source=target.source,
            name=target.name,
            source_path=target.source_path,
            error_family="missing_frontmatter",
            error_type="MissingFrontmatter",
            error_message="frontmatter must start with ---",
        )

    closing_index = -1
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            closing_index = index
            break

    if closing_index == -1:
        return FrontmatterAuditFailure(
            source=target.source,
            name=target.name,
            source_path=target.source_path,
            error_family="unterminated_frontmatter",
            error_type="UnterminatedFrontmatter",
            error_message="frontmatter block is missing the closing --- delimiter",
        )

    frontmatter_text = "\n".join(lines[1:closing_index])
    try:
        parsed = yaml.safe_load(frontmatter_text) or {}
    except yaml.YAMLError as exc:
        return FrontmatterAuditFailure(
            source=target.source,
            name=target.name,
            source_path=target.source_path,
            error_family="yaml_parse_error",
            error_type=type(exc).__name__,
            error_message=str(exc).splitlines()[0],
        )

    if not isinstance(parsed, dict):
        return FrontmatterAuditFailure(
            source=target.source,
            name=target.name,
            source_path=target.source_path,
            error_family="yaml_parse_error",
            error_type="FrontmatterNotMapping",
            error_message="frontmatter must parse to a mapping",
        )
    return None
