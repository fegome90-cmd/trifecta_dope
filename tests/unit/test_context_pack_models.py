"""Tests for Context Pack domain models."""

from dataclasses import FrozenInstanceError
import pytest
from src.domain.models import ContextPack, SourceFile, DigestEntry, ChunkMetadata, Chunk


class TestContextPackModels:
    def test_source_file_is_frozen(self) -> None:
        """SourceFile should be immutable."""
        sf = SourceFile(path="skill.md", sha256="abc123", chars=1000)
        with pytest.raises(FrozenInstanceError):
            sf.path = "other.md"  # type: ignore

    def test_source_file_no_mtime_field(self) -> None:
        """SourceFile should not have mtime field (removed for MVP)."""
        sf = SourceFile(path="skill.md", sha256="abc123", chars=1000)
        assert not hasattr(sf, "mtime")

    def test_chunk_is_frozen(self) -> None:
        """Chunk should be immutable."""
        chunk = Chunk(
            id="skill:a1b2c3d4e5",
            doc="skill",
            title="Core Rules",
            text="# Core Rules\n...",
            token_est=625,
        )
        with pytest.raises(FrozenInstanceError):
            chunk.text = "modified"  # type: ignore

    def test_chunk_metadata_is_frozen(self) -> None:
        """ChunkMetadata should be immutable."""
        meta = ChunkMetadata(id="skill:a1b2c3d4e5", doc="skill", title="Core Rules", token_est=625)
        with pytest.raises(FrozenInstanceError):
            meta.title = "modified"  # type: ignore

    def test_digest_entry_is_frozen(self) -> None:
        """DigestEntry should be immutable."""
        entry = DigestEntry(doc="skill", chunk_id="skill:a1b2c3d4e5", summary="Core rules...")
        with pytest.raises(FrozenInstanceError):
            entry.summary = "modified"  # type: ignore

    def test_context_pack_is_frozen(self) -> None:
        """ContextPack should be immutable."""
        pack = ContextPack(
            schema_version=1,
            segment_id="debug_terminal",
            created_at="2025-12-31T15:00:00Z",
            source_files=[],
            digest=[],
            index=[],
            chunks=[],
        )
        with pytest.raises(FrozenInstanceError):
            pack.segment_id = "other"  # type: ignore

    def test_context_pack_uses_segment_id_not_segment(self) -> None:
        """ContextPack should use segment_id field (not segment)."""
        pack = ContextPack(
            schema_version=1,
            segment_id="debug_terminal",
            created_at="2025-12-31T15:00:00Z",
            source_files=[],
            digest=[],
            index=[],
            chunks=[],
        )
        assert pack.segment_id == "debug_terminal"
        assert not hasattr(pack, "segment")

    def test_context_pack_schema_version_is_1(self) -> None:
        """ContextPack schema_version must be 1."""
        pack = ContextPack(
            schema_version=1,
            segment_id="test",
            created_at="2025-12-31T15:00:00Z",
            source_files=[],
            digest=[],
            index=[],
            chunks=[],
        )
        assert pack.schema_version == 1

    def test_no_embeddings_field_in_models(self) -> None:
        """No model should have embeddings/vector fields."""
        pack = ContextPack(
            schema_version=1,
            segment_id="test",
            created_at="2025-12-31T15:00:00Z",
            source_files=[],
            digest=[],
            index=[],
            chunks=[],
        )
        chunk = Chunk(id="test:abc", doc="test", title="Test", text="...", token_est=100)

        assert not hasattr(pack, "embeddings")
        assert not hasattr(chunk, "embedding")
        assert not hasattr(chunk, "vector")

    def test_context_pack_schema_no_chunking_field(self) -> None:
        """ContextPack schema v1 should NOT have top-level 'chunking' field.

        Fail-closed test: prevents drift between documented and actual schema.
        The 'chunking' field was documented in planning but never implemented.
        Actual schema uses chunking_method per chunk.
        """
        import json
        from pathlib import Path

        # Load actual context_pack.json if it exists
        pack_path = Path("_ctx/context_pack.json")
        if not pack_path.exists():
            pytest.skip("No context_pack.json found - run ctx build first")

        pack_data = json.loads(pack_path.read_text())

        # Fail-closed: schema v1 should NOT have chunking at top level
        assert "chunking" not in pack_data, (
            "Schema drift detected: 'chunking' field found in context_pack.json.\n"
            "Expected: No top-level 'chunking' field (not implemented in v1).\n"
            "Actual: 'chunking' present.\n"
            "Fix: Remove chunking from schema or implement it."
        )

    def test_source_file_has_mtime_not_mtime_epoch(self) -> None:
        """SourceFile should use 'mtime' (float), not 'mtime_epoch'.

        Fail-closed test: ensures field naming consistency.
        """
        import json
        from pathlib import Path

        pack_path = Path("_ctx/context_pack.json")
        if not pack_path.exists():
            pytest.skip("No context_pack.json found")

        pack_data = json.loads(pack_path.read_text())

        if not pack_data.get("source_files"):
            pytest.skip("No source_files in pack")

        sf = pack_data["source_files"][0]

        # Should have 'mtime' (float timestamp)
        assert "mtime" in sf, "SourceFile missing 'mtime' field"
        assert isinstance(sf["mtime"], (int, float)), "mtime should be numeric timestamp"

        # Should NOT have 'mtime_epoch'
        assert "mtime_epoch" not in sf, (
            "Schema drift: 'mtime_epoch' found. Use 'mtime' (float) instead."
        )
