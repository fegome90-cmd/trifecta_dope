"""Extended unit tests for PD Operational stop_reason precedence."""

import pytest
from pathlib import Path
from src.application.context_service import ContextService
from src.domain.context_models import ContextPack, ContextChunk, ContextIndexEntry


@pytest.fixture
def mock_context_pack_precedence(tmp_path: Path) -> Path:
    """Create a mock context pack for precedence testing."""
    ctx_dir = tmp_path / "_ctx"
    ctx_dir.mkdir()

    pack = ContextPack(
        segment="test",
        chunks=[
            ContextChunk(
                id="test:chunk1",
                doc="test",
                title_path=["chunk1.md"],
                text="# Chunk 1\n" + ("Line\n" * 100),  # ~600 chars
                char_count=600,
                token_est=150,
                source_path="chunk1.md",
            ),
            ContextChunk(
                id="test:chunk2",
                doc="test",
                title_path=["chunk2.md"],
                text="# Chunk 2\n" + ("Line\n" * 100),  # ~600 chars
                char_count=600,
                token_est=150,
                source_path="chunk2.md",
            ),
            ContextChunk(
                id="test:chunk3",
                doc="test",
                title_path=["chunk3.md"],
                text="# Chunk 3\n" + ("Line\n" * 100),  # ~600 chars
                char_count=600,
                token_est=150,
                source_path="chunk3.md",
            ),
        ],
        index=[
            ContextIndexEntry(
                id=f"test:chunk{i}",
                title_path_norm=f"chunk{i}.md",
                preview=f"# Chunk {i}",
                token_est=150,
            )
            for i in range(1, 4)
        ],
    )

    pack_path = ctx_dir / "context_pack.json"
    pack_path.write_text(pack.model_dump_json(indent=2))

    return tmp_path


def test_stop_reason_precedence_budget_over_max_chunks(mock_context_pack_precedence: Path):
    """Test that budget takes precedence over max_chunks when both conditions are met."""
    service = ContextService(mock_context_pack_precedence)

    # Trigger both conditions:
    # - max_chunks=2 (should trigger max_chunks)
    # - budget=100 (very low, should trigger budget)
    # Expected: budget wins (precedence)
    result = service.get(
        ids=["test:chunk1", "test:chunk2", "test:chunk3"],
        mode="raw",
        budget_token_est=100,  # Very low budget to force budget stop
        max_chunks=2,  # Also trigger max_chunks limit
    )

    # Budget should take precedence
    assert result.stop_reason == "budget"
    assert result.chunks_requested == 3
    # Should have stopped due to budget before hitting max_chunks limit
    assert result.chunks_returned <= 2
