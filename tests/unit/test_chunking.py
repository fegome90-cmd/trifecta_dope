"""Tests for whole-file chunking logic."""

import hashlib
import pytest
from src.application.chunking import chunk_whole_file


class TestWholeFileChunking:
    def test_chunk_id_is_deterministic(self) -> None:
        """Chunk ID should be deterministic based on content."""
        content = "# Core Rules\n\nRule 1: Test first.\n"

        chunk1 = chunk_whole_file("skill", content)
        chunk2 = chunk_whole_file("skill", content)

        assert chunk1.id == chunk2.id

    def test_chunk_id_format(self) -> None:
        """Chunk ID should follow {doc}:{sha256(text)[:10]} format."""
        content = "# Test\n\nContent here.\n"
        chunk = chunk_whole_file("skill", content)

        expected_hash = hashlib.sha256(content.encode()).hexdigest()[:10]
        expected_id = f"skill:{expected_hash}"

        assert chunk.id == expected_id

    def test_chunk_id_changes_with_content(self) -> None:
        """Different content should produce different chunk IDs."""
        chunk1 = chunk_whole_file("skill", "Content A")
        chunk2 = chunk_whole_file("skill", "Content B")

        assert chunk1.id != chunk2.id

    def test_chunk_id_changes_with_doc_name(self) -> None:
        """Different doc names should produce different chunk IDs."""
        content = "Same content"
        chunk1 = chunk_whole_file("skill", content)
        chunk2 = chunk_whole_file("agent", content)

        assert chunk1.id != chunk2.id
        assert chunk1.id.startswith("skill:")
        assert chunk2.id.startswith("agent:")

    def test_title_is_doc_name(self) -> None:
        """Title should be the doc name."""
        chunk = chunk_whole_file("skill", "# Test\n\nContent.")
        assert chunk.title == "skill"

    def test_text_is_full_content(self) -> None:
        """Text should be the full content unchanged."""
        content = "# Core Rules\n\nRule 1: Test first.\nRule 2: Keep it simple.\n"
        chunk = chunk_whole_file("skill", content)

        assert chunk.text == content

    def test_token_estimate(self) -> None:
        """Token estimate should be len(content) // 4."""
        content = "a" * 800  # 800 chars
        chunk = chunk_whole_file("skill", content)

        assert chunk.token_est == 200  # 800 // 4

    def test_token_estimate_rounds_down(self) -> None:
        """Token estimate should round down."""
        content = "a" * 803  # 803 chars
        chunk = chunk_whole_file("skill", content)

        assert chunk.token_est == 200  # 803 // 4 = 200.75 → 200

    def test_doc_field_set_correctly(self) -> None:
        """Chunk doc field should match input doc name."""
        chunk = chunk_whole_file("prime", "Content")
        assert chunk.doc == "prime"

    def test_chunk_is_immutable(self) -> None:
        """Returned chunk should be frozen."""
        from dataclasses import FrozenInstanceError

        chunk = chunk_whole_file("skill", "Content")

        with pytest.raises(FrozenInstanceError):
            chunk.text = "modified"  # type: ignore
