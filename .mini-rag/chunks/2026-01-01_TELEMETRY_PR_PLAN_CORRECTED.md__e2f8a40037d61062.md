tmp_path, level="lite")

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


class TestMonotonicTiming:
    """Test perf_counter_ns usage."""

    def test_monotonic_clock(self, tmp_path):
        """Verify timing uses perf_counter_ns."""
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
    """Test concurrent event logging (corruption-free
