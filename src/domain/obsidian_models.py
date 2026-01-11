"""Domain models for Obsidian vault integration.

This module defines the core data structures for syncing findings
to Obsidian as atomic notes with YAML frontmatter.

Following Trifecta Clean Architecture:
- Domain layer: pure data models with no external dependencies
- Frozen dataclasses for immutability
- Type-safe with Literal types where appropriate
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Optional

if TYPE_CHECKING:
    from collections.abc import Mapping


# =============================================================================
# Configuration Models
# =============================================================================


@dataclass(frozen=True)
class ObsidianConfig:
    """Configuration for Obsidian vault integration.

    Attributes:
        vault_path: Absolute path to Obsidian vault
        default_segment: Default segment to use (optional)
        min_priority: Minimum priority level to sync (P1-P5)
        note_folder: Subfolder within vault for findings
        auto_link: Whether to auto-link related notes
        date_format: Date format for note naming
    """

    vault_path: Path
    default_segment: Optional[str] = None
    min_priority: Literal["P0", "P1", "P2", "P3", "P4", "P5"] = "P5"
    note_folder: str = "Trifecta Findings"
    auto_link: bool = True
    date_format: str = "%Y-%m-%d"

    @property
    def findings_dir(self) -> Path:
        """Get the full path to the findings folder."""
        return self.vault_path / self.note_folder


# =============================================================================
# Finding Models
# =============================================================================


@dataclass(frozen=True)
class FindingAction:
    """An action item to fix a finding.

    Attributes:
        type: Action type (code, test, config, docs, etc.)
        description: What needs to be done
        files: Affected files
        estimate: Time estimate (e.g., "30 min", "2 hours")
    """

    type: Literal["code", "test", "config", "docs", "refactor", "other"]
    description: str
    files: list[str] = field(default_factory=list)
    estimate: str = "30 min"


@dataclass(frozen=True)
class FindingTraceability:
    """Traceability information for a finding.

    Attributes:
        hookify_rule: Hookify rule name (if from hookify)
        commit: Git commit SHA
        command: Command that triggered the finding
        test_command: Command to verify the fix
        location: File location (path:line)
        report_path: Path to report (e.g., MICRO_AUDIT_REPORT.md)
    """

    hookify_rule: Optional[str] = None
    commit: Optional[str] = None
    command: Optional[str] = None
    test_command: Optional[str] = None
    location: Optional[str] = None
    report_path: Optional[str] = None


@dataclass(frozen=True)
class FindingEvidence:
    """Evidence data for a finding.

    Attributes:
        pattern: The pattern that was matched
        context: Additional context (code snippet, message, etc.)
        scan_output: Output from scan tool
        tripwire_test: Tripwire test name
    """

    pattern: Optional[str] = None
    context: Optional[Mapping[str, str]] = None
    scan_output: Optional[str] = None
    tripwire_test: Optional[str] = None


@dataclass(frozen=True)
class FindingMetadata:
    """Additional metadata for a finding.

    Attributes:
        pattern_family: Pattern family (e.g., P1-Stringly-Typed)
        fix_lean_lines: Number of lines for fix_lean
        adr: ADR number (e.g., "001")
        detected_at: When the finding was detected
        detected_by: What detected it (hookify, telemetry, audit)
    """

    pattern_family: Optional[str] = None
    fix_lean_lines: Optional[int] = None
    adr: Optional[str] = None
    detected_at: Optional[str] = None
    detected_by: Literal["hookify", "telemetry", "micro-audit", "manual"] = "manual"


@dataclass(frozen=True)
class FindingRelated:
    """Related findings.

    Attributes:
        blocks: Findings this one blocks
        blocked_by: Findings blocking this one
        duplicates: Duplicate findings
        related: Other related findings
    """

    blocks: list[str] = field(default_factory=list)
    blocked_by: list[str] = field(default_factory=list)
    duplicates: list[str] = field(default_factory=list)
    related: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Finding:
    """A finding extracted from Trifecta telemetry/reports.

    This is the core domain model for all findings that will be
    synced to Obsidian as atomic notes.

    Attributes:
        id: Unique finding identifier
        title: Short descriptive title
        priority: Priority level (P1-P5, or P0 for critical)
        category: Finding category (code-quality, security, performance, etc.)
        status: Current status (open, in-progress, resolved, ignored)
        created: When finding was created
        segment: Segment name
        segment_id: Hash-based segment ID
        tags: List of tags for Obsidian
        risk: Risk description
        effort: Effort estimate (e.g., "30 min", "2 hours")
        roi: ROI description (optional)
        summary: Short summary of the finding
        description: Detailed description
        traceability: Traceability information
        evidence: Evidence data
        metadata: Additional metadata
        actions: List of actions to fix
        related: Related findings
        fix_lean: Code snippet for lean fix
    """

    id: str
    title: str
    priority: Literal["P0", "P1", "P2", "P3", "P4", "P5"]
    category: str
    status: Literal["open", "in-progress", "resolved", "ignored"]
    created: datetime
    segment: str
    segment_id: str
    tags: list[str]
    risk: str
    effort: str
    summary: str
    description: str

    # Optional fields
    roi: Optional[str] = None
    traceability: Optional[FindingTraceability] = None
    evidence: Optional[FindingEvidence] = None
    metadata: Optional[FindingMetadata] = None
    actions: list[FindingAction] = field(default_factory=list)
    related: Optional[FindingRelated] = None
    fix_lean: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "priority": self.priority,
            "category": self.category,
            "status": self.status,
            "created": self.created.isoformat(),
            "segment": self.segment,
            "segment_id": self.segment_id,
            "tags": self.tags,
            "risk": self.risk,
            "effort": self.effort,
            "summary": self.summary,
            "description": self.description,
            "roi": self.roi,
            "traceability": asdict(self.traceability) if self.traceability else None,
            "evidence": asdict(self.evidence) if self.evidence else None,
            "metadata": asdict(self.metadata) if self.metadata else None,
            "actions": [asdict(a) for a in self.actions],
            "related": asdict(self.related) if self.related else None,
            "fix_lean": self.fix_lean,
        }


# =============================================================================
# Note Models
# =============================================================================


@dataclass(frozen=True)
class ObsidianNote:
    """An Obsidian markdown note with YAML frontmatter.

    Attributes:
        path: Full path to the note file
        filename: Just the filename (without path)
        frontmatter: YAML frontmatter as dict
        content: Note body content (markdown)
        created: When note was created
        finding_id: ID of the associated finding
    """

    path: Path
    filename: str
    frontmatter: Mapping[str, object]
    content: str
    created: datetime
    finding_id: str

    def render(self) -> str:
        """Render the full note with frontmatter and content."""
        import yaml  # type: ignore

        frontmatter_str = yaml.dump(self.frontmatter, sort_keys=False, default_flow_style=False)  # type: ignore

        return f"---\n{frontmatter_str}---\n\n{self.content}"


# =============================================================================
# Sync Result Models
# =============================================================================


@dataclass(frozen=True)
class SyncResult:
    """Result of a sync operation to Obsidian.

    Attributes:
        total_findings: Total findings processed
        notes_created: Number of new notes created
        notes_updated: Number of existing notes updated
        notes_skipped: Number of findings skipped (e.g., wrong status)
        active_sources: Sources that were active (hookify, telemetry, etc.)
        duration_ms: Sync duration in milliseconds
        previews: Note previews (for dry-run mode)
    """

    total_findings: int
    notes_created: int
    notes_updated: int
    notes_skipped: int
    active_sources: list[str]
    duration_ms: int
    previews: list[dict] = field(default_factory=list)

    @property
    def total_notes(self) -> int:
        """Total notes created or updated."""
        return self.notes_created + self.notes_updated


@dataclass(frozen=True)
class ValidationResult:
    """Result of vault validation.

    Attributes:
        valid: Whether vault is valid
        writable: Whether vault is writable
        error: Error message if not valid
        findings_dir: Path to findings directory
        existing_notes: Number of existing findings notes
    """

    valid: bool
    writable: bool
    error: Optional[str] = None
    findings_dir: Optional[Path] = None
    existing_notes: int = 0
