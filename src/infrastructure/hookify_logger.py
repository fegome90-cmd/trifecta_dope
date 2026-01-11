"""Hookify Evidence Logger for Obsidian sync integration.

This module logs hookify rule violations to a JSONL file for later
synchronization to Obsidian as atomic notes.

Following Trifecta Clean Architecture:
- Infrastructure layer: handles file I/O and persistence
- Uses domain models from src.domain.obsidian_models
- Follows P3 path discipline: all operations against segment_root
"""

from __future__ import annotations

import json
import os
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Optional

if TYPE_CHECKING:
    from collections.abc import Mapping


@dataclass(frozen=True)
class HookifyViolation:
    """A single hookify rule violation event.

    Attributes:
        id: Unique violation identifier (timestamp-based)
        timestamp: ISO 8601 timestamp when violation occurred
        rule_name: Name of the hookify rule that triggered
        pattern_matched: The regex pattern that matched
        context: Additional context (file path, user message, etc.)
        status: Current status (open, resolved, ignored)
        resolved_at: Optional timestamp when resolved
    """

    id: str
    timestamp: str
    rule_name: str
    pattern_matched: str
    context: Mapping[str, str]
    status: Literal["open", "resolved", "ignored"] = "open"
    resolved_at: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "rule_name": self.rule_name,
            "pattern_matched": self.pattern_matched,
            "context": dict(self.context),
            "status": self.status,
            "resolved_at": self.resolved_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HookifyViolation":
        """Create from dictionary (JSON deserialization)."""
        if not isinstance(data, dict):
            raise TypeError(f"Expected dict, got {type(data).__name__}")

        required = ["id", "timestamp", "rule_name", "pattern_matched", "context"]
        missing = [k for k in required if k not in data]
        if missing:
            raise ValueError(f"Missing required keys: {missing}")

        if not isinstance(data["context"], dict):
            raise TypeError("context must be a dict")

        return cls(
            id=data["id"],
            timestamp=data["timestamp"],
            rule_name=data["rule_name"],
            pattern_matched=data["pattern_matched"],
            context=data["context"],
            status=data.get("status", "open"),
            resolved_at=data.get("resolved_at"),
        )


@dataclass
class HookifyEvidenceLogger:
    """Log hookify violations for later Obsidian sync.

    This logger writes violations to _ctx/hookify_violations.jsonl
    in the segment root, following P3 path discipline.

    Usage:
        logger = HookifyEvidenceLogger(segment_root)
        logger.log_violation(
            rule_name="metodo-p1-stringly-typed",
            pattern='in str(',
            context={"file": "src/main.py", "line": "42"}
        )
        violations = logger.get_violations()
    """

    segment_root: Path
    evidence_path: Path = field(init=False)
    EVIDENCE_FILE: str = field(default="_ctx/hookify_violations.jsonl", init=False, repr=False)

    def __post_init__(self):
        """Initialize evidence path after segment_root is set."""
        # P3: Resolve against segment_root, not cwd
        self.evidence_path = self.segment_root / self.EVIDENCE_FILE
        self._ensure_directory()

    def _ensure_directory(self) -> None:
        """Create evidence directory if it doesn't exist."""
        self.evidence_path.parent.mkdir(parents=True, exist_ok=True)

    def log_violation(
        self,
        rule_name: str,
        pattern: str,
        context: Mapping[str, str],
        timestamp: Optional[datetime] = None,
    ) -> HookifyViolation:
        """Log a hookify rule violation.

        Args:
            rule_name: Name of the hookify rule that triggered
            pattern: The regex pattern that matched
            context: Additional context (file path, user message, etc.)
            timestamp: When violation occurred (defaults to now)

        Returns:
            The created HookifyViolation
        """
        timestamp = timestamp or datetime.now(timezone.utc)
        # Use UUID suffix to avoid ID collisions within same second
        unique_suffix = uuid.uuid4().hex[:8]
        ts_str = timestamp.strftime("%Y%m%d%H%M%S") + "-" + unique_suffix

        violation = HookifyViolation(
            id=f"violation-{ts_str}",
            timestamp=timestamp.isoformat(),
            rule_name=rule_name,
            pattern_matched=pattern,
            context=context,
            status="open",
        )

        self._append_violation(violation)
        return violation

    def _append_violation(self, violation: HookifyViolation) -> None:
        """Append violation to JSONL file."""
        with open(self.evidence_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(violation.to_dict()) + "\n")

    def get_violations(
        self, since: Optional[datetime] = None, status: Optional[str] = None
    ) -> list[HookifyViolation]:
        """Get violations, optionally filtered.

        Args:
            since: Only return violations after this timestamp
            status: Only return violations with this status

        Returns:
            List of HookifyViolation objects
        """
        if not self.evidence_path.exists():
            return []

        violations = []
        with open(self.evidence_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    v = HookifyViolation.from_dict(json.loads(line))
                except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                    # Skip corrupted lines but continue processing
                    continue

                # Apply filters
                if since is not None:
                    v_ts = datetime.fromisoformat(v.timestamp)
                    if v_ts < since:
                        continue

                if status is not None and v.status != status:
                    continue

                violations.append(v)

        return violations

    def mark_resolved(self, violation_id: str) -> Optional[HookifyViolation]:
        """Mark a violation as resolved.

        Args:
            violation_id: ID of violation to resolve

        Returns:
            The updated violation, or None if not found
        """
        violations = self._load_all()
        updated = None

        new_violations = []
        for v in violations:
            if v.id == violation_id:
                # Create resolved version
                updated = HookifyViolation(
                    id=v.id,
                    timestamp=v.timestamp,
                    rule_name=v.rule_name,
                    pattern_matched=v.pattern_matched,
                    context=v.context,
                    status="resolved",
                    resolved_at=datetime.now(timezone.utc).isoformat(),
                )
                new_violations.append(updated)
            else:
                new_violations.append(v)

        if updated:
            self._write_all(new_violations)

        return updated

    def mark_ignored(self, violation_id: str) -> Optional[HookifyViolation]:
        """Mark a violation as ignored (won't sync to Obsidian).

        Args:
            violation_id: ID of violation to ignore

        Returns:
            The updated violation, or None if not found
        """
        violations = self._load_all()
        updated = None

        new_violations = []
        for v in violations:
            if v.id == violation_id:
                updated = HookifyViolation(
                    id=v.id,
                    timestamp=v.timestamp,
                    rule_name=v.rule_name,
                    pattern_matched=v.pattern_matched,
                    context=v.context,
                    status="ignored",
                    resolved_at=v.resolved_at,
                )
                new_violations.append(updated)
            else:
                new_violations.append(v)

        if updated:
            self._write_all(new_violations)

        return updated

    def _load_all(self) -> list[HookifyViolation]:
        """Load all violations from file."""
        if not self.evidence_path.exists():
            return []

        violations = []
        with open(self.evidence_path, "r") as f:
            for line in f:
                if not line.strip():
                    continue
                violations.append(HookifyViolation.from_dict(json.loads(line)))

        return violations

    def _write_all(self, violations: list[HookifyViolation]) -> None:
        """Write all violations back to file (atomic write).

        P4: Write to temp file, then rename to avoid partial writes.
        Uses unique temp filename to avoid collisions.
        """
        # Use tempfile.mkstemp for unique temp filename
        fd, temp_path_str = tempfile.mkstemp(
            dir=self.evidence_path.parent, prefix=self.evidence_path.name + ".", suffix=".tmp"
        )
        temp_path = Path(temp_path_str)

        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                for v in violations:
                    f.write(json.dumps(v.to_dict()) + "\n")
                f.flush()
                os.fsync(f.fileno())  # Ensure data hits disk before rename

            # Atomic rename
            temp_path.replace(self.evidence_path)
        except Exception:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise

    def clear_resolved(self) -> int:
        """Remove resolved violations from the log.

        Returns:
            Number of violations removed
        """
        violations = self._load_all()
        active = [v for v in violations if v.status != "resolved"]
        removed = len(violations) - len(active)

        if removed > 0:
            self._write_all(active)

        return removed

    def stats(self) -> dict[str, int | dict[str, int]]:
        """Get statistics about violations.

        Returns:
            Dict with counts by status and rule
        """
        violations = self._load_all()

        stats: dict[str, int | dict[str, int]] = {
            "total": len(violations),
            "open": 0,
            "resolved": 0,
            "ignored": 0,
            "by_rule": {},
        }

        for v in violations:
            current_count = stats.get(v.status, 0)
            assert isinstance(current_count, int)
            stats[v.status] = current_count + 1
            by_rule = stats["by_rule"]
            assert isinstance(by_rule, dict)
            by_rule[v.rule_name] = by_rule.get(v.rule_name, 0) + 1

        return stats
