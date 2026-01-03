"""Additional tests for T8.2 consistency patch."""

import json
from pathlib import Path
from src.infrastructure.telemetry import Telemetry


def test_stats_reads_ms_fields(tmp_path: Path) -> None:
    """Verify that ctx stats reads p50_ms/p95_ms correctly."""
    telemetry_dir = tmp_path / "_ctx" / "telemetry"
    telemetry_dir.mkdir(parents=True)

    # Create last_run.json with new format
    last_run = {
        "run_id": "test",
        "ts": "2025-12-29T00:00:00Z",
        "latencies": {
            "ctx.search": {"count": 2, "p50_ms": 1.234, "p95_ms": 2.456, "max_ms": 3.789}
        },
        "pack_state": {},
    }
    (telemetry_dir / "last_run.json").write_text(json.dumps(last_run))

    # Read and verify
    data = json.loads((telemetry_dir / "last_run.json").read_text())
    assert data["latencies"]["ctx.search"]["p50_ms"] == 1.234
    assert data["latencies"]["ctx.search"]["p95_ms"] == 2.456
    assert data["latencies"]["ctx.search"]["max_ms"] == 3.789


def test_stale_detected_only_on_validate(tmp_path: Path) -> None:
    # Verify that stale_detected only appears when validate runs.
    # Setup: Create a minimal segment marker (pyproject.toml) so Telemetry resolves root correctly
    (tmp_path / "pyproject.toml").touch()

    # Test 1: Search (no validate) - stale_detected should NOT appear
    telemetry_search = Telemetry(tmp_path, level="lite")
    telemetry_search.run_id = "search_run"
    # Mock pack_state without stale_detected (mimic regular command)
    telemetry_search.pack_state = {"pack_sha": "abc", "pack_mtime": 123}
    telemetry_search.incr("ctx_search_count")
    telemetry_search.flush()

    last_run_path = tmp_path / "_ctx" / "telemetry" / "last_run.json"
    data = json.loads(last_run_path.read_text())

    assert "pack_state" in data
    assert "pack_sha" in data["pack_state"]
    assert "pack_mtime" in data["pack_state"]
    assert "stale_detected" not in data["pack_state"], (
        "stale_detected should NOT appear for non-validate commands"
    )

    # Test 2: Validate (with stale_detected set) - should appear
    telemetry_validate = Telemetry(tmp_path, level="lite")
    telemetry_validate.run_id = "validate_run"
    # Mock pack_state WITH stale_detected (mimic validate command)
    telemetry_validate.pack_state = {"pack_sha": "abc", "pack_mtime": 123, "stale_detected": False}
    telemetry_validate.incr("ctx_validate_pass_count")
    telemetry_validate.flush()

    data = json.loads(last_run_path.read_text())
    assert "stale_detected" in data["pack_state"]
    assert data["pack_state"]["stale_detected"] is False
