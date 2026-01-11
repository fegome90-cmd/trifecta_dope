import pytest
import subprocess
import json
import os
from pathlib import Path

# Use telemetry-enabled env
ENV_WITH_PERSIST_AND_TEL = os.environ.copy()
ENV_WITH_PERSIST_AND_TEL["TRIFECTA_AST_PERSIST"] = "1"


@pytest.fixture
def fresh_cli_workspace(tmp_path):
    """
    Creates a temporary workspace with:
    - A python file to parse
    - A .trifecta directory for cache and telemetry
    """
    ws = tmp_path / "ws"
    ws.mkdir()

    # Create target file
    target = ws / "target.py"
    target.write_text("def foo():\\n    pass\\n")

    # Create ctx directories
    (ws / ".trifecta").mkdir()
    (ws / "_ctx" / "telemetry").mkdir(parents=True)

    return ws


def run_ast_symbols_with_telemetry(cwd, uri):
    """Helper to run CLI command with telemetry enabled."""
    cmd = [
        "uv",
        "run",
        "trifecta",
        "ast",
        "symbols",
        uri,
        "--segment",
        ".",
        "--telemetry",
        "lite",  # Enable telemetry
    ]

    result = subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, env=ENV_WITH_PERSIST_AND_TEL
    )
    return result


def test_ast_cache_telemetry_events(fresh_cli_workspace):
    """
    Verifies that cache operations emit telemetry events.

    Run 1: Cold start -> expect ast.cache.miss
    Run 2: Warm start -> expect ast.cache.hit
    """
    cwd = fresh_cli_workspace
    uri = "sym://python/mod/target"
    events_file = cwd / "_ctx/telemetry/events.jsonl"

    # Run 1: Cold (miss expected)
    res1 = run_ast_symbols_with_telemetry(cwd, uri)
    assert res1.returncode == 0, f"Run 1 failed: {res1.stderr}"

    # Verify events file exists
    assert events_file.exists(), "Telemetry events file not created"

    # Parse events
    events = [json.loads(line) for line in events_file.read_text().splitlines()]

    # Find cache events
    cache_events = [e for e in events if e.get("cmd", "").startswith("ast.cache.")]
    assert len(cache_events) > 0, f"No cache events found. Events: {events}"

    # Verify miss event exists
    miss_events = [e for e in events if e.get("cmd") == "ast.cache.miss"]
    assert len(miss_events) > 0, f"No ast.cache.miss events found. Cache events: {cache_events}"

    # Run 2: Warm (hit expected)
    res2 = run_ast_symbols_with_telemetry(cwd, uri)
    assert res2.returncode == 0, f"Run 2 failed: {res2.stderr}"

    # Re-parse events
    events = [json.loads(line) for line in events_file.read_text().splitlines()]
    hit_events = [e for e in events if e.get("cmd") == "ast.cache.hit"]

    assert len(hit_events) > 0, (
        f"No ast.cache.hit events found after warm run. Events: {[e.get('cmd') for e in events]}"
    )


def test_ast_cache_event_schema(fresh_cli_workspace):
    """
    Verifies telemetry events have the correct schema.

    Expected fields:
    - cmd: "ast.cache.hit" or "ast.cache.miss"
    - args.cache_key: string
    - result.backend: "SQLiteCache" or "InMemoryLRUCache"
    - result.segment_id: string
    - timing_ms: int
    """
    cwd = fresh_cli_workspace
    uri = "sym://python/mod/target"
    events_file = cwd / "_ctx/telemetry/events.jsonl"

    # Run command
    res = run_ast_symbols_with_telemetry(cwd, uri)
    assert res.returncode == 0

    # Parse events
    events = [json.loads(line) for line in events_file.read_text().splitlines()]
    cache_events = [e for e in events if e.get("cmd", "").startswith("ast.cache.")]

    assert len(cache_events) > 0, "No cache events to validate schema"

    # Validate first cache event schema
    event = cache_events[0]

    # Check required fields
    assert "cmd" in event
    assert event["cmd"] in ("ast.cache.hit", "ast.cache.miss", "ast.cache.write")

    assert "args" in event
    assert "cache_key" in event["args"]
    assert isinstance(event["args"]["cache_key"], str)

    assert "result" in event
    assert "backend" in event["result"]
    # Backend can be wrapper (FileLockedAstCache) or direct cache
    assert event["result"]["backend"] in ("SQLiteCache", "InMemoryLRUCache", "FileLockedAstCache")

    assert "segment_id" in event["result"]
    assert isinstance(event["result"]["segment_id"], str)

    assert "timing_ms" in event
    assert isinstance(event["timing_ms"], int)
    assert event["timing_ms"] > 0


def test_ast_cache_telemetry_with_persistence_off(fresh_cli_workspace):
    """
    Verifies that telemetry still works when persistence is OFF (InMemory cache).
    """
    cwd = fresh_cli_workspace
    uri = "sym://python/mod/target"
    events_file = cwd / "_ctx/telemetry/events.jsonl"

    # Use env WITHOUT persist
    env_no_persist = os.environ.copy()
    if "TRIFECTA_AST_PERSIST" in env_no_persist:
        del env_no_persist["TRIFECTA_AST_PERSIST"]

    cmd = [
        "uv",
        "run",
        "trifecta",
        "ast",
        "symbols",
        uri,
        "--segment",
        ".",
        "--telemetry",
        "lite",
    ]

    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env_no_persist)
    assert result.returncode == 0

    # Verify events file exists
    assert events_file.exists()

    # Parse events
    events = [json.loads(line) for line in events_file.read_text().splitlines()]
    cache_events = [e for e in events if e.get("cmd", "").startswith("ast.cache.")]

    assert len(cache_events) > 0, "No cache events with InMemory backend"

    # Verify backend is InMemoryLRUCache
    assert cache_events[0]["result"]["backend"] == "InMemoryLRUCache"
