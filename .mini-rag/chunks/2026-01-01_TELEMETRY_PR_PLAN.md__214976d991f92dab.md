telemetry.incr("lsp_spawn_count", 5)
        telemetry.incr("lsp_ready_count", 5)
        telemetry.incr("lsp_timeout_count", 0)
        telemetry.incr("lsp_fallback_count", 0)

        telemetry.flush()

        last_run_file = tmp_path / "_ctx" / "telemetry" / "last_run.json"
        last_run = json.loads(last_run_file.read_text())

        assert last_run["lsp"]["lsp_spawn_count"] == 5
        assert last_run["lsp"]["lsp_timeout_rate"] == 0.0

    def test_file_read_summary_calculation(self, tmp_path):
        """Verify file read bytes aggregated by mode."""
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

class TestTelemetryAggregation:
    """Test percentile calculations."""

    def test_p50_p95_calculation(self, tmp_path):
        """Verify percentile math on synthetic data."""
