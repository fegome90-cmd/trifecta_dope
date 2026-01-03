"""Unit tests for PD Operational (stop_reason + early-stop)."""

import pytest
from pathlib import Path
from src.application.context_service import ContextService
from src.domain.context_models import ContextPack, ContextChunk, ContextIndexEntry


@pytest.fixture
def mock_context_pack(tmp_path: Path) -> Path:
    """Create a mock context pack with multiple chunks."""
    ctx_dir = tmp_path / "_ctx"
    ctx_dir.mkdir()

    pack = ContextPack(
        segment="test",
        chunks=[
            ContextChunk(
                id="test:chunk1",
                doc="test",
                title_path=["chunk1.md"],
                text="# Chunk 1\n" + ("Line\n" * 50),  # ~300 chars
                char_count=300,
                token_est=75,
                source_path="chunk1.md",
            ),
            ContextChunk(
                id="test:chunk2",
                doc="test",
                title_path=["chunk2.md"],
                text="# Chunk 2\n" + ("Line\n" * 50),  # ~300 chars
                char_count=300,
                token_est=75,
                source_path="chunk2.md",
            ),
            ContextChunk(
                id="test:chunk3",
                doc="test",
                title_path=["chunk3.md"],
                text="# Chunk 3\n" + ("Line\n" * 50),  # ~300 chars
                char_count=300,
                token_est=75,
                source_path="chunk3.md",
            ),
            ContextChunk(
                id="test:chunk4",
                doc="test",
                title_path=["chunk4.md"],
                text="# Chunk 4\n" + ("Line\n" * 50),  # ~300 chars
                char_count=300,
                token_est=75,
                source_path="chunk4.md",
            ),
            ContextChunk(
                id="test:chunk5",
                doc="test",
                title_path=["chunk5.md"],
                text="# Chunk 5\n" + ("Line\n" * 50),  # ~300 chars
                char_count=300,
                token_est=75,
                source_path="chunk5.md",
            ),
        ],
        index=[
            ContextIndexEntry(
                id=f"test:chunk{i}",
                title_path_norm=f"chunk{i}.md",
                preview=f"# Chunk {i}",
                token_est=75,
            )
            for i in range(1, 6)
        ],
    )

    pack_path = ctx_dir / "context_pack.json"
    pack_path.write_text(pack.model_dump_json(indent=2))

    return tmp_path


def test_stop_reason_complete(mock_context_pack: Path):
    """Test that stop_reason is 'complete' when all chunks are processed without budget issues."""
    service = ContextService(mock_context_pack)

    result = service.get(
        ids=["test:chunk1"],
        mode="excerpt",
        budget_token_est=1000,
        max_chunks=None,
    )

    assert result.stop_reason == "complete"
    assert result.chunks_requested == 1
    assert result.chunks_returned == 1
    assert result.chars_returned_total > 0


def test_stop_reason_budget(mock_context_pack: Path):
    """Test that stop_reason is 'budget' when budget is exceeded."""
    service = ContextService(mock_context_pack)

    result = service.get(
        ids=["test:chunk1", "test:chunk2", "test:chunk3", "test:chunk4", "test:chunk5"],
        mode="raw",
        budget_token_est=100,  # Very low budget
        max_chunks=None,
    )

    assert result.stop_reason == "budget"
    assert result.chunks_requested == 5
    assert result.chunks_returned < result.chunks_requested
    assert result.chars_returned_total > 0


def test_stop_reason_max_chunks(mock_context_pack: Path):
    """Test that stop_reason is 'max_chunks' when max_chunks limit is applied."""
    service = ContextService(mock_context_pack)

    result = service.get(
        ids=["test:chunk1", "test:chunk2", "test:chunk3", "test:chunk4", "test:chunk5"],
        mode="excerpt",
        budget_token_est=5000,  # High budget
        max_chunks=2,
    )

    assert result.stop_reason == "max_chunks"
    assert result.chunks_requested == 5
    assert result.chunks_returned == 2
    assert result.chars_returned_total > 0


def test_chars_returned_tracking(mock_context_pack: Path):
    """Test that chars_returned_total accurately tracks returned content."""
    service = ContextService(mock_context_pack)

    result = service.get(
        ids=["test:chunk1", "test:chunk2"],
        mode="excerpt",
        budget_token_est=1000,
        max_chunks=None,
    )

    # Calculate expected chars from returned chunks
    expected_chars = sum(len(chunk.text) for chunk in result.chunks)

    assert result.chars_returned_total == expected_chars
    assert result.chars_returned_total > 0
    assert result.stop_reason == "complete"
