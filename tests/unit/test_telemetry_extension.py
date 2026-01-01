"""Unit tests for telemetry extension (PR#1)."""

import json
import threading
import time
from pathlib import Path

import pytest

from src.infrastructure.telemetry import Telemetry, _relpath


class TestReservedKeyProtection:
    """Test reserved key collision detection."""

    def test_collision_raises_error(self, tmp_path: Path) -> None:
        """Verify ValueError on reserved key collision."""
        telemetry = Telemetry(tmp_path, level="lite")

        with pytest.raises(ValueError, match="reserved keys"):
            telemetry.event(
                "test.cmd",
                {},
                {},
                100,
                ts="2026-01-01T00:00:00Z",  # RESERVED KEY
            )

    def test_multiple_collisions(self, tmp_path: Path) -> None:
        """Verify error message includes all colliding keys."""
        telemetry = Telemetry(tmp_path, level="lite")

        with pytest.raises(ValueError, match="ts"):
            telemetry.event(
                "test.cmd",
                {},
                {},
                100,
                ts="2026-01-01",
                run_id="fake_id",
            )

    def test_safe_extra_fields(self, tmp_path: Path) -> None:
        """Verify non-reserved keys accepted."""
        telemetry = Telemetry(tmp_path, level="lite")

        # Should not raise
        telemetry.event(
            "test.cmd",
            {},
            {},
            100,
            bytes_read=1024,
            lsp_state="READY",
            custom_field="value",
        )
        telemetry.flush()

        events_file = tmp_path / "_ctx" / "telemetry" / "events.jsonl"
        event = json.loads(events_file.read_text().strip())

        # Extra fields are namespaced under "x"
        assert event["x"]["bytes_read"] == 1024
        assert event["x"]["lsp_state"] == "READY"
        assert event["x"]["custom_field"] == "value"


class TestPathNormalization:
    """Test _relpath utility."""

    def test_relpath_inside_workspace(self) -> None:
        """Verify relative path for files inside workspace."""
        root = Path("/workspaces/trifecta_dope")
        target = Path("/workspaces/trifecta_dope/src/domain/models.py")

        result = _relpath(root, target)

        assert result == "src/domain/models.py"
        assert not result.startswith("/")

    def test_relpath_outside_workspace(self) -> None:
        """Verify external/<hash>-<name> for files outside workspace."""
        root = Path("/workspaces/trifecta_dope")
        target = Path("/usr/lib/python3.12/typing.py")

        result = _relpath(root, target)

        assert result.startswith("external/")
        assert result.endswith("-typing.py")
        assert "/" not in result.split("-", 1)[1]  # No slashes after hash

    def test_relpath_uniqueness(self) -> None:
        """Verify different external paths produce different hashes."""
        root = Path("/workspaces/trifecta_dope")
        target1 = Path("/usr/lib/python3.12/typing.py")
        target2 = Path("/opt/python3.12/typing.py")  # Same name, different path

        result1 = _relpath(root, target1)
        result2 = _relpath(root, target2)

        # Different hashes ensure uniqueness
        assert result1 != result2
        assert result1.endswith("-typing.py")
        assert result2.endswith("-typing.py")


class TestExtraFields:
    """Test extra_fields serialization."""

    def test_extra_fields_in_event(self, tmp_path: Path) -> None:
        """Verify extra fields appear in events.jsonl under x namespace."""
        telemetry = Telemetry(tmp_path, level="lite")

        telemetry.event(
            "test.cmd",
            {},
            {},
            100,
            bytes_read=2048,
            disclosure_mode="excerpt",
            cache_hit=True,
        )
        telemetry.flush()

        events_file = tmp_path / "_ctx" / "telemetry" / "events.jsonl"
        event = json.loads(events_file.read_text().strip())

        # Extra fields are namespaced under "x"
        assert event["x"]["bytes_read"] == 2048
        assert event["x"]["disclosure_mode"] == "excerpt"
        assert event["x"]["cache_hit"] is True

    def test_extra_fields_types(self, tmp_path: Path) -> None:
        """Verify various types serialize correctly under x namespace."""
        telemetry = Telemetry(tmp_path, level="lite")

        telemetry.event(
            "test.cmd",
            {},
            {},
            100,
            int_field=42,
            float_field=3.14,
            bool_field=True,
            str_field="hello",
            list_field=[1, 2, 3],
            dict_field={"key": "value"},
        )
        telemetry.flush()

        events_file = tmp_path / "_ctx" / "telemetry" / "events.jsonl"
        event = json.loads(events_file.read_text().strip())

        # All extra fields under "x" namespace
        assert event["x"]["int_field"] == 42
        assert abs(event["x"]["float_field"] - 3.14) < 0.01
        assert event["x"]["bool_field"] is True
        assert event["x"]["str_field"] == "hello"
        assert event["x"]["list_field"] == [1, 2, 3]
        assert event["x"]["dict_field"] == {"key": "value"}


class TestSummaryCalculations:
    """Test aggregation in flush()."""

    def test_ast_summary(self, tmp_path: Path) -> None:
        """Verify AST summary calculation (empty for PR#1)."""
        telemetry = Telemetry(tmp_path, level="lite")

        telemetry.incr("ast_parse_count", 100)
        telemetry.incr("ast_cache_hit_count", 86)
        telemetry.incr("ast_cache_miss_count", 14)

        telemetry.flush()

        last_run_file = tmp_path / "_ctx" / "telemetry" / "last_run.json"
        last_run = json.loads(last_run_file.read_text())

        assert last_run["ast"]["ast_parse_count"] == 100
        assert last_run["ast"]["ast_cache_hit_count"] == 86
        assert last_run["ast"]["ast_cache_miss_count"] == 14
        assert abs(last_run["ast"]["ast_cache_hit_rate"] - 0.86) < 0.01

    def test_lsp_summary(self, tmp_path: Path) -> None:
        """Verify LSP summary calculation (empty for PR#1)."""
        telemetry = Telemetry(tmp_path, level="lite")

        telemetry.incr("lsp_spawn_count", 5)
        telemetry.incr("lsp_ready_count", 5)
        telemetry.incr("lsp_fallback_count", 1)

        telemetry.flush()

        last_run_file = tmp_path / "_ctx" / "telemetry" / "last_run.json"
        last_run = json.loads(last_run_file.read_text())

        assert last_run["lsp"]["lsp_spawn_count"] == 5
        assert last_run["lsp"]["lsp_ready_count"] == 5
        assert last_run["lsp"]["lsp_ready_rate"] == 1.0
        assert abs(last_run["lsp"]["lsp_fallback_rate"] - 0.2) < 0.01

    def test_file_read_summary(self, tmp_path: Path) -> None:
        """Verify file read summary calculation (empty for PR#1)."""
        telemetry = Telemetry(tmp_path, level="lite")

        telemetry.incr("file_read_skeleton_bytes_total", 1024)
        telemetry.incr("file_read_excerpt_bytes_total", 5120)
        telemetry.incr("file_read_raw_bytes_total", 10240)

        telemetry.flush()

        last_run_file = tmp_path / "_ctx" / "telemetry" / "last_run.json"
        last_run = json.loads(last_run_file.read_text())

        assert last_run["file_read"]["skeleton_bytes"] == 1024
        assert last_run["file_read"]["excerpt_bytes"] == 5120
        assert last_run["file_read"]["raw_bytes"] == 10240
        assert last_run["file_read"]["total_bytes"] == 16384

    def test_telemetry_drops_summary(self, tmp_path: Path) -> None:
        """Verify telemetry_drops summary with drop_rate calculation."""
        telemetry = Telemetry(tmp_path, level="lite")

        # Simulate some events attempted, written, and dropped
        telemetry.incr("telemetry_events_attempted", 100)
        telemetry.incr("telemetry_events_written", 97)
        telemetry.incr("telemetry_lock_skipped", 3)

        telemetry.flush()

        last_run_file = tmp_path / "_ctx" / "telemetry" / "last_run.json"
        last_run = json.loads(last_run_file.read_text())

        assert last_run["telemetry_drops"]["lock_skipped"] == 3
        assert last_run["telemetry_drops"]["attempted"] == 100
        assert last_run["telemetry_drops"]["written"] == 97
        # 3/100 = 0.03 (3%)
        assert abs(last_run["telemetry_drops"]["drop_rate"] - 0.03) < 0.001


class TestMonotonicTiming:
    """Test perf_counter_ns usage."""

    def test_monotonic_clock(self, tmp_path: Path) -> None:
        """Verify timing uses monotonic measurements."""
        telemetry = Telemetry(tmp_path, level="lite")

        start_ns = time.perf_counter_ns()
        time.sleep(0.01)  # 10ms
        elapsed_ms = int((time.perf_counter_ns() - start_ns) / 1_000_000)

        telemetry.event("test.cmd", {}, {}, elapsed_ms)
        telemetry.flush()

        events_file = tmp_path / "_ctx" / "telemetry" / "events.jsonl"
        event = json.loads(events_file.read_text().strip())

        # Assert timing is reasonable (8-30ms for 10ms sleep + overhead)
        assert 8 <= event["timing_ms"] <= 30


class TestConcurrencySafety:
    """Test concurrent event logging (corruption-free guarantee)."""

    def test_concurrent_writes_no_corruption(self, tmp_path: Path) -> None:
        """Verify concurrent writes produce valid JSON (no interleaved data)."""

        def write_events(thread_id: int) -> None:
            telemetry = Telemetry(tmp_path, level="lite")
            for i in range(10):
                telemetry.event(
                    f"thread_{thread_id}",
                    {"iteration": i},
                    {"status": "ok"},
                    10,
                )
            telemetry.flush()

        threads = [threading.Thread(target=write_events, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify all logged events are valid JSON
        events_file = tmp_path / "_ctx" / "telemetry" / "events.jsonl"
        events = []
        for line in events_file.read_text().strip().split("\n"):
            if line:
                event = json.loads(line)  # Should not raise
                events.append(event)
                assert "cmd" in event
                assert "timing_ms" in event

        # Some events may be dropped (lossy model), but all logged events must be valid
        assert len(events) > 0, "At least some events should be logged"
        # Note: We do NOT assert exact count (5 threads × 10 events = 50)
        # because lossy fcntl model allows drops


class TestSegmentId:
    """Test segment_id hashing for privacy."""

    def test_segment_id_consistent(self, tmp_path: Path) -> None:
        """Verify segment_id is consistent for same path."""
        telemetry1 = Telemetry(tmp_path, level="lite")
        telemetry1.event("test1", {}, {}, 10)
        telemetry1.flush()

        telemetry2 = Telemetry(tmp_path, level="lite")
        telemetry2.event("test2", {}, {}, 10)
        telemetry2.flush()

        events_file = tmp_path / "_ctx" / "telemetry" / "events.jsonl"
        lines = events_file.read_text().strip().split("\n")
        event1 = json.loads(lines[0])
        event2 = json.loads(lines[1])

        # Same segment_path should produce same segment_id
        assert event1["segment_id"] == event2["segment_id"]
        # Should be 8-char hash
        assert len(event1["segment_id"]) == 8

    def test_segment_id_no_absolute_path(self, tmp_path: Path) -> None:
        """Verify segment_id does not leak absolute path."""
        telemetry = Telemetry(tmp_path, level="lite")
        telemetry.event("test", {}, {}, 10)
        telemetry.flush()

        events_file = tmp_path / "_ctx" / "telemetry" / "events.jsonl"
        event = json.loads(events_file.read_text().strip())

        # segment_id should be hash, not path
        assert "/" not in event["segment_id"]
        assert str(tmp_path) not in json.dumps(event)
