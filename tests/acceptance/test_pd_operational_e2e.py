"""E2E acceptance test for PD Operational (CLI to telemetry)."""

import json
import subprocess
from pathlib import Path
import pytest


@pytest.fixture
def test_segment(tmp_path: Path) -> Path:
    """Create a minimal test segment with context pack."""
    from src.domain.context_models import ContextPack, ContextChunk, ContextIndexEntry

    segment = tmp_path / "test_segment"
    segment.mkdir()
    ctx_dir = segment / "_ctx"
    ctx_dir.mkdir()

    # Create minimal context pack
    pack = ContextPack(
        segment="test_segment",
        chunks=[
            ContextChunk(
                id="test:chunk1",
                doc="test",
                title_path=["chunk1.md"],
                text="# Test Chunk 1\nContent for testing",
                char_count=35,
                token_est=10,
                source_path="chunk1.md",
            ),
            ContextChunk(
                id="test:chunk2",
                doc="test",
                title_path=["chunk2.md"],
                text="# Test Chunk 2\nMore content",
                char_count=30,
                token_est=8,
                source_path="chunk2.md",
            ),
        ],
        index=[
            ContextIndexEntry(
                id=f"test:chunk{i}",
                title_path_norm=f"chunk{i}.md",
                preview=f"# Test Chunk {i}",
                token_est=10,
            )
            for i in range(1, 3)
        ],
    )

    pack_path = ctx_dir / "context_pack.json"
    pack_path.write_text(pack.model_dump_json(indent=2))

    return segment


def test_e2e_max_chunks_via_cli(test_segment: Path):
    """E2E test: CLI invocation with --max-chunks produces correct telemetry."""
    # Run the actual CLI command
    result = subprocess.run(
        [
            "uv",
            "run",
            "trifecta",
            "ctx",
            "get",
            "--segment",
            str(test_segment),
            "--ids",
            "test:chunk1,test:chunk2",
            "--max-chunks",
            "1",
            "--mode",
            "excerpt",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"CLI failed: {result.stderr}"

    # Verify output contains exactly 1 chunk
    output = result.stdout
    assert "Retrieved 1 chunk(s)" in output
    assert "test:chunk1" in output
    # Should NOT contain chunk2 (early-stopped)
    assert "test:chunk2" not in output

    # Verify telemetry file contains correct data
    telemetry_events_path = test_segment / "_ctx" / "telemetry" / "events.jsonl"
    if telemetry_events_path.exists():
        events = []
        with open(telemetry_events_path) as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))

        # Find the ctx.get event
        get_events = [e for e in events if e.get("event_name") == "ctx.get"]
        assert len(get_events) > 0, "No ctx.get events found in telemetry"

        last_event = get_events[-1]
        result_data = last_event.get("result", {})

        # Validate telemetry payload
        assert result_data.get("stop_reason") == "max_chunks"
        assert result_data.get("chunks_requested") == 2
        assert result_data.get("chunks_returned") == 1
        assert result_data.get("chars_returned_total", 0) > 0


def test_e2e_no_max_chunks_complete(test_segment: Path):
    """E2E test: Without --max-chunks, should return all chunks with stop_reason=complete."""
    result = subprocess.run(
        [
            "uv",
            "run",
            "trifecta",
            "ctx",
            "get",
            "--segment",
            str(test_segment),
            "--ids",
            "test:chunk1,test:chunk2",
            "--mode",
            "excerpt",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0

    # Should retrieve both chunks
    output = result.stdout
    assert "Retrieved 2 chunk(s)" in output
    assert "test:chunk1" in output
    assert "test:chunk2" in output

    # Check telemetry for stop_reason=complete
    telemetry_events_path = test_segment / "_ctx" / "telemetry" / "events.jsonl"
    if telemetry_events_path.exists():
        events = []
        with open(telemetry_events_path) as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))

        get_events = [e for e in events if e.get("event_name") == "ctx.get"]
        if get_events:
            last_event = get_events[-1]
            result_data = last_event.get("result", {})
            assert result_data.get("stop_reason") == "complete"
            assert result_data.get("chunks_requested") == 2
            assert result_data.get("chunks_returned") == 2
