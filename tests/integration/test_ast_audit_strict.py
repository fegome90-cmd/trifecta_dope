import json
import subprocess
import pytest
from pathlib import Path


def test_events_jsonl_schema_complete():
    """T2.1: Events must have full PR#1 schema."""
    # Trigger a real event
    subprocess.run(
        [
            "uv",
            "run",
            "python",
            "-m",
            "src.infrastructure.cli",
            "ast",
            "symbols",
            "sym://python/mod/src/infrastructure/cli_ast",
            "--segment",
            ".",
            "--telemetry",
            "full",
        ],
        check=True,
        capture_output=True,
    )

    events_path = Path("_ctx/telemetry/events.jsonl")
    assert events_path.exists()

    lines = events_path.read_text().strip().splitlines()
    assert len(lines) > 0, "No events generated"

    last_event = json.loads(lines[-1])

    # Strictly required top-level keys
    required_keys = {
        "ts",
        "run_id",
        "segment_id",
        "cmd",
        "args",
        "result",
        "timing_ms",
        "warnings",
        "x",
    }

    missing = required_keys - last_event.keys()
    assert not missing, f"Event missing keys: {missing}"

    # Mode prohibition check
    if "x" in last_event and "mode" in last_event["x"]:
        assert last_event["x"]["mode"] != "text", "Found forbidden mode='text'!"


def test_last_run_has_summaries():
    """T2.2: last_run.json must have ast, file_read, telemetry_drops."""
    # Ensure run exists
    last_run_path = Path("_ctx/telemetry/last_run.json")
    if not last_run_path.exists():
        subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "src.infrastructure.cli",
                "ast",
                "symbols",
                "sym://python/mod/src/infrastructure/cli_ast",
                "--segment",
                ".",
                "--telemetry",
                "full",
            ],
            check=True,
        )

    data = json.loads(last_run_path.read_text())

    assert "ast" in data, "Missing 'ast' summary"
    assert "file_read" in data, "Missing 'file_read' summary"
    assert "telemetry_drops" in data, "Missing 'telemetry_drops' summary"
    assert "lock_skipped" in data["telemetry_drops"], "Missing 'lock_skipped' in telemetry_drops"


def test_error_shape_is_strict():
    """T2.3: Error response must have full shape."""
    result = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "-m",
            "src.infrastructure.cli",
            "ast",
            "symbols",
            "sym://python/mod/nonexistent",
            "--segment",
            ".",
            "--telemetry",
            "lite",
        ],
        capture_output=True,
        text=True,
    )

    resp = json.loads(result.stdout)

    assert resp["status"] == "error"
    assert "kind" in resp
    assert "data" in resp
    assert "refs" in resp
    assert "errors" in resp
    assert "next_actions" in resp

    assert resp["data"] is None
    assert isinstance(resp["refs"], list)
    assert len(resp["errors"]) > 0
