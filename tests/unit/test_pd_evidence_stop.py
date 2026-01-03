"""Unit tests for evidence-based early-stop."""

import pytest
from pathlib import Path
from src.application.context_service import ContextService
from src.domain.context_models import ContextPack, ContextChunk, ContextIndexEntry


@pytest.fixture
def mock_context_pack_with_evidence(tmp_path: Path) -> Path:
    """Create a mock context pack with evidence-bearing chunks."""
    ctx_dir = tmp_path / "_ctx"
    ctx_dir.mkdir()

    pack = ContextPack(
        segment="test",
        chunks=[
            # Chunk 1: Has both strong_hit (prime + query) and support (def pattern)
            ContextChunk(
                id="prime:chunk1",
                doc="prime",
                title_path=["LSPClient"],
                text="# LSPClient\ndef LSPClient(socket_path):\n    pass\nclass Helper:\n    pass",
                char_count=100,
                token_est=25,
                source_path="lsp_client.py",
            ),
            # Chunk 2: Has strong_hit but NO support
            ContextChunk(
                id="prime:chunk2",
                doc="prime",
                title_path=["Config"],
                text="# Config\nConfiguration for the system\nNo code definitions here",
                char_count=80,
                token_est=20,
                source_path="config.md",
            ),
            # Chunk 3: Regular chunk without evidence
            ContextChunk(
                id="test:chunk3",
                doc="test",
                title_path=["utils.py"],
                text="# Utils\ndef helper():\n    pass",
                char_count=50,
                token_est=12,
                source_path="utils.py",
            ),
        ],
        index=[
            ContextIndexEntry(
                id="prime:chunk1",
                title_path_norm="LSPClient",
                preview="# LSPClient",
                token_est=25,
            ),
            ContextIndexEntry(
                id="prime:chunk2",
                title_path_norm="Config",
                preview="# Config",
                token_est=20,
            ),
            ContextIndexEntry(
                id="test:chunk3",
                title_path_norm="utils.py",
                preview="# Utils",
                token_est=12,
            ),
        ],
    )

    pack_path = ctx_dir / "context_pack.json"
    pack_path.write_text(pack.model_dump_json(indent=2))

    return tmp_path


def test_evidence_stop_strong_hit_plus_support(mock_context_pack_with_evidence: Path):
    """Test that stop_reason='evidence' when both strong_hit and support are present."""
    service = ContextService(mock_context_pack_with_evidence)

    result = service.get(
        ids=["prime:chunk1", "prime:chunk2", "test:chunk3"],
        mode="raw",
        budget_token_est=5000,  # High budget to avoid budget stop
        max_chunks=None,  # No max_chunks limit
        stop_on_evidence=True,
        query="LSPClient",  # Matches chunk1
    )

    assert result.stop_reason == "evidence"
    assert result.chunks_returned == 1  # Should stop after first chunk
    assert result.evidence_metadata["strong_hit"] is True
    assert result.evidence_metadata["support"] is True


def test_evidence_stop_strong_hit_only(mock_context_pack_with_evidence: Path):
    """Test that evidence-stop does NOT trigger with only strong_hit (no support)."""
    service = ContextService(mock_context_pack_with_evidence)

    result = service.get(
        ids=["prime:chunk2", "test:chunk3"],  # chunk2 has strong_hit but no support
        mode="raw",
        budget_token_est=5000,
        max_chunks=None,
        stop_on_evidence=True,
        query="Config",  # Matches chunk2 title, but no def/class in text
    )

    # Should NOT stop on evidence (missing support), should complete normally
    assert result.stop_reason == "complete"
    assert result.chunks_returned == 2  # Should process both chunks


def test_evidence_stop_disabled_by_default(mock_context_pack_with_evidence: Path):
    """Test that evidence-stop is disabled by default (stop_on_evidence=False)."""
    service = ContextService(mock_context_pack_with_evidence)

    result = service.get(
        ids=["prime:chunk1", "prime:chunk2", "test:chunk3"],
        mode="raw",
        budget_token_est=5000,
        max_chunks=None,
        stop_on_evidence=False,  # Explicitly disabled
        query="LSPClient",  # Would trigger evidence if enabled
    )

    # Should NOT stop on evidence, should process all chunks
    assert result.stop_reason == "complete"
    assert result.chunks_returned == 3
    # Evidence metadata should remain default (not checked)
    assert result.evidence_metadata["strong_hit"] is False
    assert result.evidence_metadata["support"] is False
