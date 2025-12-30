"""T8 Observability Test Suite."""

import json
import tempfile
from pathlib import Path

import pytest

from src.infrastructure.telemetry import Telemetry


def test_telemetry_off_writes_nothing(tmp_path):
    """Verify that telemetry=off creates no files."""
    telemetry = Telemetry(tmp_path, level="off")
    telemetry.event("test", {}, {}, 100)
    telemetry.incr("test_counter")
    telemetry.flush()
    
    telemetry_dir = tmp_path / "_ctx" / "telemetry"
    assert not telemetry_dir.exists(), "Telemetry dir should not exist when level=off"


def test_events_jsonl_appends(tmp_path):
    """Verify that events are appended to events.jsonl."""
    telemetry = Telemetry(tmp_path, level="lite", run_id="test_run")
    
    telemetry.event("ctx.search", {"query": "test"}, {"hits": 3}, 42)
    telemetry.event("ctx.get", {"ids": ["id1"]}, {"chunks": 1}, 20)
    telemetry.flush()
    
    events_path = tmp_path / "_ctx" / "telemetry" / "events.jsonl"
    assert events_path.exists()
    
    lines = events_path.read_text().strip().split("\n")
    assert len(lines) == 2
    
    event1 = json.loads(lines[0])
    assert event1["cmd"] == "ctx.search"
    assert event1["run_id"] == "test_run"
    assert event1["timing_ms"] == 42


def test_events_rotation(tmp_path):
    """Verify that events.jsonl rotates at 5MB."""
    telemetry = Telemetry(tmp_path, level="lite")
    
    # Write a large event to exceed 5MB
    large_payload = "x" * (6 * 1024 * 1024)  # 6MB
    telemetry.event("large", {"data": large_payload}, {}, 0)
    telemetry.flush()
    
    events_path = tmp_path / "_ctx" / "telemetry" / "events.jsonl"
    backup_path = tmp_path / "_ctx" / "telemetry" / "events.1.jsonl"
    
    # After rotation, the original should be renamed
    assert backup_path.exists() or events_path.stat().st_size < 6 * 1024 * 1024


def test_metrics_flush_creates_files(tmp_path):
    """Verify that flush() creates metrics.json and last_run.json."""
    telemetry = Telemetry(tmp_path, level="lite", run_id="flush_test")
    
    telemetry.incr("ctx_build_count", 5)
    telemetry.incr("ctx_search_count", 10)
    telemetry.observe("ctx.search", 100)
    telemetry.observe("ctx.search", 200)
    telemetry.flush()
    
    metrics_path = tmp_path / "_ctx" / "telemetry" / "metrics.json"
    last_run_path = tmp_path / "_ctx" / "telemetry" / "last_run.json"
    
    assert metrics_path.exists()
    assert last_run_path.exists()
    
    metrics = json.loads(metrics_path.read_text())
    assert metrics["ctx_build_count"] == 5
    assert metrics["ctx_search_count"] == 10
    
    last_run = json.loads(last_run_path.read_text())
    assert last_run["run_id"] == "flush_test"
    assert "ctx.search" in last_run["latencies"]
    assert last_run["latencies"]["ctx.search"]["p50_ms"] in [100.0, 200.0]


def test_ctx_search_emits_event_and_counts(tmp_path):
    """Verify that SearchUseCase records telemetry correctly."""
    from src.application.search_get_usecases import SearchUseCase
    
    # Setup a minimal context pack
    ctx_dir = tmp_path / "_ctx"
    ctx_dir.mkdir()
    
    pack_data = {
        "schema_version": 1,
        "segment": "test",
        "source_files": [],
        "chunks": [],
        "index": [
            {"id": "skill:abc", "title_path_norm": "skill.md", "preview": "test content", "token_est": 100}
        ]
    }
    (ctx_dir / "context_pack.json").write_text(json.dumps(pack_data))
    
    telemetry = Telemetry(tmp_path, level="lite")
    use_case = SearchUseCase(None, telemetry)  # fs not used
    
    output = use_case.execute(tmp_path, "test", limit=5)
    telemetry.flush()
    
    metrics = json.loads((tmp_path / "_ctx" / "telemetry" / "metrics.json").read_text())
    assert metrics["ctx_search_count"] == 1
    assert metrics["ctx_search_hits_total"] == 1


def test_ctx_get_records_budget_trim(tmp_path):
    """Verify that GetChunkUseCase records budget_trim_count."""
    from src.application.search_get_usecases import GetChunkUseCase
    
    # Setup context pack with a large chunk
    ctx_dir = tmp_path / "_ctx"
    ctx_dir.mkdir()
    
    large_text = "x" * 10000  # ~2500 tokens
    pack_data = {
        "schema_version": 1,
        "segment": "test",
        "source_files": [],
        "chunks": [
            {
                "id": "skill:abc",
                "doc": "skill",
                "title_path": ["skill.md"],
                "text": large_text,
                "char_count": len(large_text),
                "token_est": 2500,
                "source_path": "skill.md",
                "chunking_method": "whole_file"
            }
        ],
        "index": []
    }
    (ctx_dir / "context_pack.json").write_text(json.dumps(pack_data))
    
    telemetry = Telemetry(tmp_path, level="lite")
    use_case = GetChunkUseCase(None, telemetry)  # fs not used
    
    # Request with low budget to trigger trim
    output = use_case.execute(tmp_path, ["skill:abc"], mode="raw", budget_token_est=500)
    telemetry.flush()
    
    metrics = json.loads((tmp_path / "_ctx" / "telemetry" / "metrics.json").read_text())
    assert metrics["ctx_get_count"] == 1
    assert metrics.get("ctx_get_budget_trim_count", 0) == 1
