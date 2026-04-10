"""
SkillHubIndexingStrategy - Manifest-driven indexing for skill_hub segments.

Contract:
- Only entries in skills_manifest.json are indexed
- Segment metadata files are excluded
- Files in repo but not in manifest are excluded
- Fail-closed if manifest invalid

Author: Trifecta Team
Date: 2026-03-19
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path

from src.domain.context_models import ContextChunk, ContextPack, ContextIndexEntry, SourceFile
from src.domain.result import Err, Ok, Result
from src.domain.segment_indexing_policy import SegmentIndexingPolicy
from src.domain.skill_manifest import SkillManifest

logger = logging.getLogger(__name__)


class SkillHubIndexingStrategy:
    """
    Manifest-driven indexing strategy for skill_hub segments.

    Only indexes skills listed in skills_manifest.json.
    Excludes segment metadata files (skill.md, prime_*.md, etc).
    Fail-closed if manifest is invalid.
    """

    def __init__(self, segment_path: Path, segment_id: str | None = None) -> None:
        """
        Initialize strategy.

        Args:
            segment_path: Path to segment root directory
            segment_id: Optional segment ID. If None, reads from trifecta_config.json
        """
        self.segment_path = segment_path
        self.ctx_dir = segment_path / "_ctx"

        # Derive segment_id: explicit param > config > directory name
        if segment_id is not None:
            self.segment_id = segment_id
        else:
            self.segment_id = self._read_segment_id_from_config()

    def _read_segment_id_from_config(self) -> str:
        """Read segment_id from trifecta_config.json, fallback to directory name.

        The config model (TrifectaConfig) stores the canonical field as 'segment'.
        We check 'segment' first (canonical), then 'segment_id' (legacy compat).
        The returned value is normalized to a segment_id via the naming module.
        """
        config_path = self.ctx_dir / "trifecta_config.json"
        if config_path.exists():
            try:
                data = json.loads(config_path.read_text(encoding="utf-8"))
                # Canonical field: 'segment' (TrifectaConfig.segment)
                if "segment" in data:
                    return str(data["segment"])
                # Legacy compat: 'segment_id'
                if "segment_id" in data:
                    return str(data["segment_id"])
            except (json.JSONDecodeError, OSError):
                pass
        return self.segment_path.name

    def build(self) -> Result[ContextPack, list[str]]:
        """
        Build context pack for skill_hub segment.

        Returns:
            Ok(ContextPack) if valid
            Err(list[str]) if invalid

        Fail-closed: Any validation error returns Err.
        """
        # 1. Verify policy is skill_hub
        policy = SegmentIndexingPolicy.detect(self.segment_path)
        if policy != SegmentIndexingPolicy.SKILL_HUB:
            return Err(
                [
                    f"Invalid indexing policy '{policy}' for SkillHubIndexingStrategy. "
                    f"Expected '{SegmentIndexingPolicy.SKILL_HUB}'."
                ]
            )

        # 2. Load and validate manifest
        manifest_path = self.ctx_dir / "skills_manifest.json"
        manifest_result = SkillManifest.load(manifest_path, self.segment_path)

        if isinstance(manifest_result, Err):
            return manifest_result

        manifest = manifest_result.value
        return self.build_from_manifest(manifest)

    def build_from_manifest(self, manifest: SkillManifest) -> Result[ContextPack, list[str]]:
        """Build context pack from an already-admitted manifest."""
        # 2.5 Verify policy is still skill_hub (defense in depth)
        policy = SegmentIndexingPolicy.detect(self.segment_path)
        if policy != SegmentIndexingPolicy.SKILL_HUB:
            return Err(
                [
                    f"Invalid indexing policy '{policy}' for SkillHubIndexingStrategy. "
                    f"Expected '{SegmentIndexingPolicy.SKILL_HUB}'."
                ]
            )

        # 3. Build chunks only from manifest entries
        errors: list[str] = []
        chunks: list[ContextChunk] = []
        index_entries: list[ContextIndexEntry] = []
        source_files: list[SourceFile] = []
        skipped_non_canonical: list[str] = []  # Track skipped entries for observability

        for skill_entry in manifest.skills:
            # Skip non-canonical skills
            if not skill_entry.canonical:
                skipped_non_canonical.append(skill_entry.name)
                continue

            # Read skill file
            skill_file_path = self.segment_path / skill_entry.relative_path
            if not skill_file_path.exists():
                errors.append(f"Skill file not found: {skill_entry.relative_path}")
                continue

            content = skill_file_path.read_text(encoding="utf-8")
            if not content.endswith("\n"):
                content += "\n"

            # Build source file metadata
            sha256 = hashlib.sha256(content.encode()).hexdigest()
            mtime = skill_file_path.stat().st_mtime
            source_files.append(
                SourceFile(
                    path=skill_entry.relative_path,
                    sha256=sha256,
                    mtime=mtime,
                    chars=len(content),
                )
            )

            # Build chunk
            chunk_id = skill_entry.chunk_id  # Already includes content hash
            chunk = ContextChunk(
                id=chunk_id,
                doc="skill",
                title_path=[skill_file_path.name],
                text=content,
                char_count=len(content),
                token_est=len(content) // 4,  # Simple token estimation
                source_path=skill_entry.relative_path,
                chunking_method="whole_file",
            )
            chunks.append(chunk)

            # Build index entry
            preview = content[:200].strip() + "..." if len(content) > 200 else content
            index_entry = ContextIndexEntry(
                id=chunk_id,
                title_path_norm=skill_file_path.name,
                preview=preview,
                token_est=chunk.token_est,
            )
            index_entries.append(index_entry)

        if errors:
            return Err(errors)

        # 3.5 Report skipped entries for observability
        if skipped_non_canonical:
            logger.info(
                f"SkillHubIndexing: Skipped {len(skipped_non_canonical)} non-canonical skills: "
                f"{', '.join(skipped_non_canonical[:5])}"
                f"{'...' if len(skipped_non_canonical) > 5 else ''}"
            )

        # 4. Build context pack
        pack = ContextPack(
            schema_version=1,
            segment=self.segment_id,
            created_at=datetime.now().isoformat(),
            digest="",
            source_files=source_files,
            chunks=chunks,
            index=index_entries,
        )

        return Ok(pack)
