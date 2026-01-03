"""Hookify violation extractor for Obsidian sync.

This module extracts findings from hookify violations and converts
them to Finding objects for Obsidian note generation.

Following Trifecta Clean Architecture:
- Application layer: orchestrates data transformation
- Uses domain models from src.domain.obsidian_models
- Uses infrastructure from src.infrastructure.hookify_logger
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Mapping

from src.domain.obsidian_models import (
    Finding,
    FindingAction,
    FindingEvidence,
    FindingMetadata,
    FindingRelated,
    FindingTraceability,
)
from src.infrastructure.hookify_logger import HookifyViolation

if TYPE_CHECKING:
    pass


# =============================================================================
# Rule Metadata Registry
# =============================================================================


@dataclass(frozen=True)
class RuleMetadata:
    """Metadata for a hookify rule.

    Attributes:
        priority: Priority level (P1-P5)
        category: Finding category
        pattern_family: Pattern family name
        adr: ADR number (if applicable)
        risk_template: Risk description template
        fix_template: Fix description template
        effort: Default effort estimate
    """

    priority: Literal["P1", "P2", "P3", "P4", "P5"]
    category: str
    pattern_family: str
    adr: str | None
    risk_template: str
    fix_template: str
    effort: str


# Rule metadata for /metodo patterns
RULE_METADATA: Mapping[str, RuleMetadata] = {
    "metodo-p1-stringly-typed": RuleMetadata(
        priority="P1",
        category="code-quality",
        pattern_family="P1-Stringly-Typed",
        adr="001",
        risk_template="Brittle parsing under refactors can cause silent failures",
        fix_template="Replace string matching with type-based error handling",
        effort="30 min",
    ),
    "metodo-p2-non-deterministic": RuleMetadata(
        priority="P2",
        category="testing",
        pattern_family="P2-Non-Deterministic",
        adr="001",
        risk_template="Flaky tests cause CI failures and false positives",
        fix_template="Remove timing dependencies, use contract-based testing",
        effort="1 hour",
    ),
    "metodo-p3-cwd-coupling": RuleMetadata(
        priority="P3",
        category="path-discipline",
        pattern_family="P3-CWD-Coupling",
        adr="001",
        risk_template="Path coupling causes failures in different execution contexts",
        fix_template="Use absolute paths from segment_root",
        effort="20 min",
    ),
    "metodo-p4-concurrency-noise": RuleMetadata(
        priority="P4",
        category="concurrency",
        pattern_family="P4-Concurrency-Noise",
        adr="001",
        risk_template="Race conditions cause intermittent failures and stderr pollution",
        fix_template="Add lifecycle hardening and proper shutdown protocols",
        effort="2 hours",
    ),
    "metodo-p5-env-precedence": RuleMetadata(
        priority="P5",
        category="configuration",
        pattern_family="P5-Env-Precedence",
        adr="001",
        risk_template="Unclear precedence causes unpredictable behavior",
        fix_template="Document precedence table and test config overrides",
        effort="30 min",
    ),
    "hardcoded-secrets": RuleMetadata(
        priority="P0",
        category="security",
        pattern_family="Security-Hardcoded-Secrets",
        adr=None,
        risk_template="CRITICAL: Hardcoded secrets exposed in code",
        fix_template="Remove secret, use environment variables, rotate credential",
        effort="1 hour",
    ),
    "debug-code-left-in": RuleMetadata(
        priority="P5",
        category="code-quality",
        pattern_family="Debug-Code",
        adr=None,
        risk_template="Debug code reduces code quality and performance",
        fix_template="Remove debug statements before commit",
        effort="10 min",
    ),
}


# =============================================================================
# Hookify Extractor
# =============================================================================


@dataclass
class HookifyExtractor:
    """Extract findings from hookify violations.

    Converts HookifyViolation objects to Finding objects for Obsidian
    note generation, applying rule metadata and context.

    Usage:
        extractor = HookifyExtractor()
        violations = logger.get_violations()
        findings = extractor.extract(violations, segment_root)
    """

    def __init__(self, segment_root: Path):
        """Initialize extractor.

        Args:
            segment_root: Root path of the segment (for segment_id)
        """
        from src.infrastructure.segment_utils import compute_segment_id

        self.segment_root = segment_root
        self.segment_id = compute_segment_id(segment_root)

    def extract(
        self,
        violations: list[HookifyViolation],
        min_priority: Literal["P0", "P1", "P2", "P3", "P4", "P5"] = "P5",
    ) -> list[Finding]:
        """Extract findings from violations.

        Args:
            violations: List of hookify violations
            min_priority: Minimum priority to include

        Returns:
            List of Finding objects
        """
        findings = []

        for violation in violations:
            # Skip ignored violations
            if violation.status == "ignored":
                continue

            # Get rule metadata
            metadata = RULE_METADATA.get(violation.rule_name)
            if not metadata:
                # Unknown rule - skip or log warning
                continue

            # Filter by priority
            if not self._priority_meets_min(metadata.priority, min_priority):
                continue

            # Convert violation to finding
            finding = self._violation_to_finding(violation, metadata)
            findings.append(finding)

        return findings

    def _priority_meets_min(
        self,
        priority: Literal["P0", "P1", "P2", "P3", "P4", "P5"],
        min_priority: Literal["P1", "P2", "P3", "P4", "P5"],
    ) -> bool:
        """Check if priority meets minimum threshold.

        P0 is highest, P5 is lowest.
        """
        priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "P4": 4, "P5": 5}

        return priority_order.get(priority, 99) <= priority_order.get(min_priority, 5)

    def _violation_to_finding(
        self, violation: HookifyViolation, rule_meta: RuleMetadata
    ) -> Finding:
        """Convert a violation to a Finding.

        Args:
            violation: Hookify violation
            rule_meta: Rule metadata

        Returns:
            Finding object
        """
        # Generate title from rule and pattern
        title = self._generate_title(violation, rule_meta)

        # Generate tags
        tags = self._generate_tags(violation, rule_meta)

        # Generate traceability
        traceability = FindingTraceability(
            hookify_rule=violation.rule_name,
            location=violation.context.get("file_path"),
            command=violation.context.get("command"),
        )

        # Generate evidence
        evidence = FindingEvidence(
            pattern=violation.pattern_matched,
            context=violation.context,
        )

        # Generate metadata
        finding_metadata = FindingMetadata(
            pattern_family=rule_meta.pattern_family,
            adr=rule_meta.adr,
            detected_at=violation.timestamp,
            detected_by="hookify",
        )

        # Generate action
        action = FindingAction(
            type="code" if rule_meta.category == "code-quality" else "other",
            description=rule_meta.fix_template,
            estimate=rule_meta.effort,
        )

        return Finding(
            id=violation.id,
            title=title,
            priority=rule_meta.priority,
            category=rule_meta.category,
            status=violation.status,  # open, resolved
            created=datetime.fromisoformat(violation.timestamp),
            segment=self.segment_root.name,
            segment_id=self.segment_id,
            tags=tags,
            risk=rule_meta.risk_template,
            effort=rule_meta.effort,
            summary=f"Violation of {violation.rule_name}: {rule_meta.risk_template}",
            description=self._generate_description(violation, rule_meta),
            traceability=traceability,
            evidence=evidence,
            metadata=finding_metadata,
            actions=[action],
            related=FindingRelated(),
        )

    def _generate_title(self, violation: HookifyViolation, rule_meta: RuleMetadata) -> str:
        """Generate finding title."""
        rule_name = violation.rule_name.replace("-", " ").replace("_", " ").title()
        return f"[{rule_meta.priority}] {rule_name}"

    def _generate_tags(self, violation: HookifyViolation, rule_meta: RuleMetadata) -> list[str]:
        """Generate Obsidian tags."""
        tags = [
            f"finding/{rule_meta.priority}",
            f"pattern/{rule_meta.pattern_family}",
            "source/hookify",
            f"category/{rule_meta.category}",
        ]

        if rule_meta.adr:
            tags.append(f"adr/{rule_meta.adr}")

        return tags

    def _generate_description(self, violation: HookifyViolation, rule_meta: RuleMetadata) -> str:
        """Generate finding description."""
        lines = [
            f"**Rule**: `{violation.rule_name}`",
            f"**Pattern**: `{violation.pattern_matched}`",
            "",
            f"**Risk**: {rule_meta.risk_template}",
            "",
            "**Fix**:",
            f"- {rule_meta.fix_template}",
            f"- Estimated effort: {rule_meta.effort}",
        ]

        # Add context if available
        if violation.context:
            lines.extend(
                [
                    "",
                    "**Context**:",
                ]
            )
            for key, value in violation.context.items():
                if value:
                    lines.append(f"- `{key}`: {value}")

        return "\n".join(lines)
