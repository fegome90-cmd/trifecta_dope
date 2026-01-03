"""Obsidian sync use case.

This module orchestrates the end-to-end sync of findings to Obsidian,
following Trifecta's Clean Architecture use case pattern.

Following Trifecta Clean Architecture:
- Application layer: orchestrates business logic
- Uses domain models from src.domain.obsidian_models
- Delegates to infrastructure for I/O
- Delegates to application services for transformation
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from src.domain.obsidian_models import (
    Finding,
    ObsidianConfig,
    SyncResult,
    ValidationResult,
)
from src.application.hookify_extractor import HookifyExtractor
from src.application.obsidian_renderer import NoteRenderer
from src.infrastructure.hookify_logger import HookifyEvidenceLogger
from src.infrastructure.obsidian_config import ObsidianConfigManager
from src.infrastructure.obsidian_writer import ObsidianWriter

if TYPE_CHECKING:
    from collections.abc import Mapping


@dataclass
class SyncToObsidianUseCase:
    """Use case for syncing findings to Obsidian vault.

    This is the main orchestration layer that coordinates:
    1. Loading configuration
    2. Extracting findings from various sources
    3. Filtering by priority
    4. Rendering notes
    5. Writing to vault (or preview if dry-run)

    Usage:
        use_case = SyncToObsidianUseCase(config)
        result = use_case.execute(
            segment_path=Path("."),
            min_priority="P2",
            dry_run=False,
            sources={"hookify": True, "telemetry": False}
        )
    """

    config: ObsidianConfig
    renderer: NoteRenderer = field(init=False)
    writer: ObsidianWriter = field(init=False)
    config_manager: ObsidianConfigManager = field(init=False)

    def __post_init__(self):
        """Initialize dependencies after config is set."""
        self.renderer = NoteRenderer(date_format=self.config.date_format)
        self.writer = ObsidianWriter(self.config)
        self.config_manager = ObsidianConfigManager()

    def execute(
        self,
        segment_path: Path,
        min_priority: Literal["P0", "P1", "P2", "P3", "P4", "P5"] = "P5",
        dry_run: bool = False,
        sources: Mapping[str, bool] | None = None,
    ) -> SyncResult:
        """Execute the sync use case.

        Args:
            segment_path: Path to segment root
            min_priority: Minimum priority to sync (P1-P5)
            dry_run: If True, preview without writing
            sources: Which sources to include (default: all)

        Returns:
            SyncResult with summary
        """
        start_time = time.time()

        # Default sources
        if sources is None:
            sources = {
                "hookify": True,
                "telemetry": True,
                "micro_audit": True,
            }

        # Validate vault
        validation = self.writer.validate_vault()
        if not validation.valid:
            raise RuntimeError(f"Vault validation failed: {validation.error}")

        # Extract findings from all enabled sources
        all_findings: list[Finding] = []
        active_sources: list[str] = []

        if sources.get("hookify", False):
            hookify_findings = self._extract_hookify_findings(segment_path, min_priority)
            all_findings.extend(hookify_findings)
            if hookify_findings:
                active_sources.append("hookify")

        if sources.get("telemetry", False):
            # TODO: Implement telemetry extraction
            pass

        if sources.get("micro_audit", False):
            # TODO: Implement micro-audit extraction
            pass

        # Get existing note IDs to avoid duplicates
        existing_ids = self.writer.get_existing_note_ids()

        # Filter out already-synced findings
        new_findings = [f for f in all_findings if f.id not in existing_ids]

        # Render notes
        notes = [self.renderer.render(f, self.config.vault_path) for f in new_findings]

        # Track results
        notes_created = 0
        notes_updated = 0
        notes_skipped = len(all_findings) - len(new_findings)

        previews: list[dict] = []

        if dry_run:
            # Generate previews
            for note in notes:
                previews.append(
                    {
                        "path": str(note.path),
                        "content": note.render()[:500] + "...",
                        "finding_id": note.finding_id,
                    }
                )
        else:
            # Write notes
            batch_result = self.writer.write_batch(notes)
            notes_created = batch_result.created
            notes_updated = batch_result.updated

            if batch_result.failed > 0:
                # Log errors but don't fail the sync
                for error in batch_result.errors:
                    print(f"Warning: {error}")

        duration_ms = int((time.time() - start_time) * 1000)

        return SyncResult(
            total_findings=len(all_findings),
            notes_created=notes_created,
            notes_updated=notes_updated,
            notes_skipped=notes_skipped,
            active_sources=active_sources,
            duration_ms=duration_ms,
            previews=previews,
        )

    def _extract_hookify_findings(
        self,
        segment_path: Path,
        min_priority: Literal["P0", "P1", "P2", "P3", "P4", "P5"],
    ) -> list[Finding]:
        """Extract findings from hookify violations.

        Args:
            segment_path: Path to segment root
            min_priority: Minimum priority to include

        Returns:
            List of Finding objects
        """
        # Initialize logger
        logger = HookifyEvidenceLogger(segment_path)

        # Get violations
        violations = logger.get_violations()

        # Extract findings
        extractor = HookifyExtractor(segment_path)
        findings = extractor.extract(violations, min_priority)

        return findings

    def validate_vault(self) -> ValidationResult:
        """Validate the Obsidian vault configuration.

        Convenience method that delegates to the writer.

        Returns:
            ValidationResult with outcome
        """
        return self.writer.validate_vault()

    def show_config(self) -> str:
        """Show current configuration.

        Convenience method that delegates to the config manager.

        Returns:
            Formatted configuration string
        """
        return self.config_manager.show()


def create_sync_use_case(
    vault_path: Path | None = None,
    min_priority: Literal["P0", "P1", "P2", "P3", "P4", "P5"] = "P5",
) -> SyncToObsidianUseCase:
    """Factory function to create a sync use case.

    Loads configuration with proper precedence and creates
    the use case with all dependencies.

    Args:
        vault_path: Optional vault path override
        min_priority: Optional min priority override

    Returns:
        Configured SyncToObsidianUseCase
    """
    config_manager = ObsidianConfigManager()
    config = config_manager.load(vault_path=vault_path, min_priority=min_priority)

    return SyncToObsidianUseCase(config=config)
