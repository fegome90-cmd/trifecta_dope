```python
"""Unit tests for AST/LSP telemetry instrumentation."""

import json
import time
from pathlib import Path
import pytest
from src.infrastructure.telemetry import Telemetry

class TestTelemetryExtension:
    """Test telemetry.event() extended fields."""

    def test_extra_fields_serialized(self, tmp_path):
        """Verify extra fields appear in events.jsonl."""
        telemetry = Telemetry(tmp_path, level="lite")

        telemetry.event(
            "test.command",
            {"arg": "value"},
            {"result": "ok"},
            100,
            bytes_read=1024,           # NEW
            disclosure_mode="excerpt", # NEW
            cache_hit=True,            # NEW
        )
        telemetry.flush()

        events_file = tmp_path / "_ctx" / "telemetry" / "events.jsonl"
        event = json.loads(events_file.read_text().strip().split("\n")[0])

        assert event["bytes_read"] == 1024
        assert event["disclosure_mode"] == "excerpt"
        assert event["cache_hit"] is True

    def test_monotonic_timing(self, tmp_path):
        """Verify timing uses perf_counter_ns (monotonic)."""
        telemetry = Telemetry(tmp_path, level="lite")

        start_ns = time.perf_counter_ns()
        time.sleep(0.01)  # 10ms
        elapsed_ms = int((time.perf_counter_ns() - start_ns) / 1_000_000)

        telemetry.event(
            "test.command",
            {},
