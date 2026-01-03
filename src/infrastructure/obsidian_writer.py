"""Obsidian vault writer.

This module handles writing notes to the Obsidian vault, following
Trifecta's path discipline (P3) and atomic write patterns (P4).

Following Trifecta Clean Architecture:
- Infrastructure layer: handles file I/O and persistence
- Uses domain models from src.domain.obsidian_models
- P3: All operations against vault_path, not cwd
- P4: Atomic writes with temp file + rename
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from src.domain.obsidian_models import ObsidianConfig, ObsidianNote, ValidationResult

if TYPE_CHECKING:
    pass


@dataclass(frozen=True)
class WriteResult:
    """Result of writing a single note.

    Attributes:
        note_path: Path where note was written
        created: True if note was created, False if updated
        existing_path: If updated, path to previous version
    """

    note_path: Path
    created: bool
    existing_path: Path | None = None


@dataclass(frozen=True)
class BatchResult:
    """Result of writing multiple notes.

    Attributes:
        total: Total notes attempted
        created: Number of new notes created
        updated: Number of existing notes updated
        failed: Number of writes that failed
        errors: List of error messages
    """

    total: int
    created: int
    updated: int
    failed: int
    errors: list[str] = field(default_factory=list)


class ObsidianWriter:
    """Write notes to Obsidian vault.

    Handles atomic writes, directory creation, and vault validation.

    Usage:
        writer = ObsidianWriter(vault_path)
        result = writer.write(note)
        batch_result = writer.write_batch([note1, note2])
        validation = writer.validate_vault()
    """

    def __init__(self, vault_path: Path | ObsidianConfig):
        """Initialize writer.

        Args:
            vault_path: Path to Obsidian vault (or ObsidianConfig)
        """
        if isinstance(vault_path, ObsidianConfig):
            self.vault_path = vault_path.vault_path
            self.findings_dir = vault_path.findings_dir
        else:
            self.vault_path = vault_path
            self.findings_dir = vault_path / "Trifecta Findings"

    def write(self, note: ObsidianNote) -> WriteResult:
        """Write a single note to the vault.

        Creates parent directories if needed. Uses atomic write pattern
        (write to temp, then rename) for P4 compliance.

        Args:
            note: Note to write

        Returns:
            WriteResult with outcome

        Raises:
            OSError: If write fails
        """
        # Ensure directory exists
        self._ensure_directory()

        # Full path to note
        note_path = self.findings_dir / note.filename

        # Check if note exists
        existing_path = None
        created = not note_path.exists()

        if not created:
            existing_path = note_path

        # P4: Atomic write pattern with fsync
        # Write to temp file, flush to disk, then rename
        temp_path = note_path.with_suffix(".tmp")

        try:
            content = note.render()
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())  # Ensure data hits disk before rename

            # Atomic rename
            temp_path.replace(note_path)

        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise OSError(f"Failed to write note {note.filename}: {e}") from e

        return WriteResult(
            note_path=note_path,
            created=created,
            existing_path=existing_path,
        )

    def write_batch(self, notes: list[ObsidianNote]) -> BatchResult:
        """Write multiple notes to the vault.

        Args:
            notes: List of notes to write

        Returns:
            BatchResult with summary
        """
        total = len(notes)
        created = 0
        updated = 0
        failed = 0
        errors: list[str] = []

        for note in notes:
            try:
                result = self.write(note)
                if result.created:
                    created += 1
                else:
                    updated += 1
            except Exception as e:
                failed += 1
                errors.append(f"{note.filename}: {e}")

        return BatchResult(
            total=total,
            created=created,
            updated=updated,
            failed=failed,
            errors=errors,
        )

    def _ensure_directory(self) -> None:
        """Create findings directory if it doesn't exist."""
        self.findings_dir.mkdir(parents=True, exist_ok=True)

    def validate_vault(self) -> ValidationResult:
        """Validate vault is accessible and writable.

        Checks:
        - Vault path exists
        - Vault is a directory
        - Vault is writable
        - Findings directory can be created

        Returns:
            ValidationResult with outcome
        """
        # Check vault exists
        if not self.vault_path.exists():
            return ValidationResult(
                valid=False,
                writable=False,
                error=f"Vault path does not exist: {self.vault_path}",
                findings_dir=None,
                existing_notes=0,
            )

        # Check vault is a directory
        if not self.vault_path.is_dir():
            return ValidationResult(
                valid=False,
                writable=False,
                error=f"Vault path is not a directory: {self.vault_path}",
                findings_dir=None,
                existing_notes=0,
            )

        # Check vault is writable
        if not os.access(self.vault_path, os.W_OK):
            return ValidationResult(
                valid=False,
                writable=False,
                error=f"Vault path is not writable: {self.vault_path}",
                findings_dir=self.findings_dir,
                existing_notes=0,
            )

        # Check findings directory
        if self.findings_dir.exists():
            if not self.findings_dir.is_dir():
                return ValidationResult(
                    valid=False,
                    writable=False,
                    error=f"Findings path exists but is not a directory: {self.findings_dir}",
                    findings_dir=self.findings_dir,
                    existing_notes=0,
                )
        else:
            # Try to create it
            try:
                self._ensure_directory()
            except OSError as e:
                return ValidationResult(
                    valid=False,
                    writable=False,
                    error=f"Cannot create findings directory: {e}",
                    findings_dir=self.findings_dir,
                    existing_notes=0,
                )

        # Count existing notes
        existing_notes = self._count_existing_notes()

        return ValidationResult(
            valid=True,
            writable=True,
            error=None,
            findings_dir=self.findings_dir,
            existing_notes=existing_notes,
        )

    def _count_existing_notes(self) -> int:
        """Count existing finding notes.

        Returns:
            Number of .md files in findings directory
        """
        if not self.findings_dir.exists():
            return 0

        return len(list(self.findings_dir.glob("*.md")))

    def get_existing_note_ids(self) -> set[str]:
        """Get IDs of existing notes.

        Reads existing notes and extracts finding IDs from frontmatter.

        Returns:
            Set of finding IDs that already have notes
        """
        if not self.findings_dir.exists():
            return set()

        existing_ids = set()

        for note_path in self.findings_dir.glob("*.md"):
            try:
                # Read frontmatter
                with open(note_path, encoding="utf-8") as f:
                    lines = f.readlines()

                # Find id field in frontmatter
                for line in lines:
                    if line.strip().startswith("id:"):
                        # Extract ID value
                        id_value = line.split(":", 1)[1].strip().strip("\"'")
                        existing_ids.add(id_value)
                        break
            except Exception:
                # Skip files that can't be read
                continue

        return existing_ids

    def delete_note(self, finding_id: str) -> bool:
        """Delete a note by finding ID.

        Args:
            finding_id: ID of finding to delete

        Returns:
            True if note was deleted, False if not found
        """
        if not self.findings_dir.exists():
            return False

        for note_path in self.findings_dir.glob("*.md"):
            try:
                with open(note_path, encoding="utf-8") as f:
                    content = f.read()

                # Check if this is the right note
                if f'id: "{finding_id}"' in content or f"id: '{finding_id}'" in content:
                    note_path.unlink()
                    return True

            except Exception:
                continue

        return False
