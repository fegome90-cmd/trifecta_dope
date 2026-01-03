"""Obsidian note renderer with YAML frontmatter.

This module renders Finding objects as Obsidian markdown notes with
YAML frontmatter for Dataview queries and linking.

Following Trifecta Clean Architecture:
- Application layer: handles data transformation and rendering
- Uses domain models from src.domain.obsidian_models
- Pure function: no side effects, just data → string
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from src.domain.obsidian_models import Finding, ObsidianNote

if TYPE_CHECKING:
    from collections.abc import Mapping


class NoteRenderer:
    """Render Obsidian notes from findings.

    Converts Finding objects to ObsidianNote instances with properly
    formatted YAML frontmatter and markdown body.

    Usage:
        renderer = NoteRenderer()
        note = renderer.render(finding, vault_path)
        note_content = note.render()
    """

    def __init__(self, date_format: str = "%Y-%m-%d"):
        """Initialize renderer.

        Args:
            date_format: Date format for note filenames
        """
        self.date_format = date_format

    def render(self, finding: Finding, vault_path: Path) -> ObsidianNote:
        """Render a finding as an Obsidian note.

        Args:
            finding: The finding to render
            vault_path: Path to Obsidian vault (for relative paths)

        Returns:
            ObsidianNote instance
        """
        filename = self._generate_filename(finding)
        note_path = vault_path / "Trifecta Findings" / filename

        frontmatter = self._render_frontmatter(finding)
        content = self._render_body(finding)

        return ObsidianNote(
            path=note_path,
            filename=filename,
            frontmatter=frontmatter,
            content=content,
            created=datetime.now(timezone.utc),
            finding_id=finding.id,
        )

    def _generate_filename(self, finding: Finding) -> str:
        """Generate note filename from finding.

        Format: {date}-{priority}-{id}.md
        Example: 2026-01-03-P1-violation-20260103120000.md
        """
        date_str = finding.created.strftime(self.date_format)
        # Sanitize title for filename
        return f"{date_str}-{finding.priority}-{finding.id}.md"

    def _render_frontmatter(self, finding: Finding) -> Mapping[str, object]:
        """Render YAML frontmatter from finding.

        Returns:
            Dictionary compatible with YAML dump
        """
        frontmatter: dict[str, object] = {
            "id": finding.id,
            "title": finding.title,
            "created": finding.created.isoformat(),
            "segment": finding.segment,
            "segment_id": finding.segment_id,
            "priority": finding.priority,
            "status": finding.status,
            "tags": finding.tags,
            "category": finding.category,
            "effort": finding.effort,
            "risk": finding.risk,
        }

        # Add optional fields
        if finding.roi:
            frontmatter["roi"] = finding.roi

        # Traceability
        if finding.traceability:
            trace: dict[str, str | None] = {}
            if finding.traceability.hookify_rule:
                trace["hookify_rule"] = finding.traceability.hookify_rule
            if finding.traceability.commit:
                trace["commit"] = finding.traceability.commit
            if finding.traceability.command:
                trace["command"] = finding.traceability.command
            if finding.traceability.test_command:
                trace["test_command"] = finding.traceability.test_command
            if finding.traceability.location:
                trace["location"] = finding.traceability.location
            if finding.traceability.report_path:
                trace["report_path"] = finding.traceability.report_path
            if trace:
                frontmatter["traceability"] = trace

        # Evidence
        if finding.evidence:
            evidence: dict[str, str | Mapping[str, str] | None] = {}
            if finding.evidence.pattern:
                evidence["pattern"] = finding.evidence.pattern
            if finding.evidence.context:
                evidence["context"] = finding.evidence.context
            if finding.evidence.scan_output:
                evidence["scan_output"] = finding.evidence.scan_output
            if finding.evidence.tripwire_test:
                evidence["tripwire_test"] = finding.evidence.tripwire_test
            if evidence:
                frontmatter["evidence"] = evidence

        # Metadata
        if finding.metadata:
            meta: dict[str, str | None] = {}
            if finding.metadata.pattern_family:
                meta["pattern_family"] = finding.metadata.pattern_family
            if finding.metadata.fix_lean_lines:
                meta["fix_lean_lines"] = finding.metadata.fix_lean_lines
            if finding.metadata.adr:
                meta["adr"] = finding.metadata.adr
            meta["detected_at"] = finding.metadata.detected_at or finding.created.isoformat()
            meta["detected_by"] = finding.metadata.detected_by
            frontmatter["metadata"] = meta

        # Actions
        if finding.actions:
            actions_list = [
                {
                    "type": action.type,
                    "description": action.description,
                    "files": action.files,
                    "estimate": action.estimate,
                }
                for action in finding.actions
            ]
            frontmatter["actions"] = actions_list

        # Related
        if finding.related:
            related: dict[str, list[str]] = {}
            if finding.related.blocks:
                related["blocks"] = finding.related.blocks
            if finding.related.blocked_by:
                related["blocked_by"] = finding.related.blocked_by
            if finding.related.duplicates:
                related["duplicates"] = finding.related.duplicates
            if finding.related.related:
                related["related"] = finding.related.related
            if related:
                frontmatter["related"] = related

        # Links (reference strings, not wiki-links for portability)
        links: dict[str, str] = {}
        links["segment_name"] = finding.segment
        links["segment_id"] = finding.segment_id

        if finding.metadata and finding.metadata.adr:
            links["adr_reference"] = f"ADR-{finding.metadata.adr}"

        frontmatter["links"] = links

        return frontmatter

    def _render_body(self, finding: Finding) -> str:
        """Render note body content.

        Returns:
            Markdown content for the note body
        """
        lines = [
            f"# {finding.title}",
            "",
            "## Summary",
            finding.summary,
            "",
            "## Risk",
            finding.risk,
            "",
        ]

        # Pattern detected
        lines.extend(
            [
                "## Pattern Detected",
            ]
        )

        if finding.traceability and finding.traceability.hookify_rule:
            lines.append(f"**Hookify Rule**: `{finding.traceability.hookify_rule}`")

        if finding.evidence and finding.evidence.pattern:
            lines.append(f"**Pattern**: `{finding.evidence.pattern}`")

        lines.append("")

        # Evidence
        lines.extend(
            [
                "## Evidence",
            ]
        )

        if finding.evidence and finding.evidence.context:
            lines.append("**Context**:")
            lines.append("```")
            for key, value in finding.evidence.context.items():
                if value:
                    lines.append(f"{key}: {value}")
            lines.append("```")
            lines.append("")

        if finding.traceability and finding.traceability.location:
            lines.append(f"**Location**: `{finding.traceability.location}`")
            lines.append("")

        # Fix lean
        if finding.fix_lean:
            lines.extend(
                [
                    "## Fix Lean",
                    f"**Estimated Effort**: {finding.effort}",
                    "```python",
                    finding.fix_lean,
                    "```",
                    "",
                ]
            )

        # Actions
        if finding.actions:
            lines.extend(
                [
                    "## Actions",
                ]
            )
            for i, action in enumerate(finding.actions, 1):
                lines.append(f"{i}. [ ] **{action.type}**: {action.description}")
                if action.files:
                    lines.append(f"   - Files: {', '.join(action.files)}")
                lines.append(f"   - Estimate: {action.estimate}")
            lines.append("")

        # Traceability
        lines.extend(
            [
                "## Traceability",
                f"- **Detected**: {finding.created.isoformat()}",
                f"- **Source**: `{finding.metadata.detected_by if finding.metadata else 'unknown'}`",
                f"- **Segment**: `{finding.segment}` (ID: `{finding.segment_id}`)",
                f"- **Priority**: `{finding.priority}`",
                "",
            ]
        )

        # Related
        if finding.related:
            related_items = []
            if finding.related.blocks:
                related_items.extend(f"[[{id}]]" for id in finding.related.blocks)
            if finding.related.blocked_by:
                related_items.extend(f"[[{id}]]" for id in finding.related.blocked_by)
            if finding.related.related:
                related_items.extend(f"[[{id}]]" for id in finding.related.related)

            if related_items:
                lines.extend(
                    [
                        "## Related",
                    ]
                )
                for related_id in related_items:
                    lines.append(f"- {related_id}")
                lines.append("")

        # Description (detailed)
        lines.extend(
            [
                "## Details",
                finding.description,
                "",
            ]
        )

        return "\n".join(lines)
