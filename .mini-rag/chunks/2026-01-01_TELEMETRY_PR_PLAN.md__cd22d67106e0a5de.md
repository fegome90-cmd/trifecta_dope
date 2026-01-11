telemetry.event(
            "test.command",
            {},
            {},
            elapsed_ms,
        )
        telemetry.flush()

        events_file = tmp_path / "_ctx" / "telemetry" / "events.jsonl"
        event = json.loads(events_file.read_text().strip().split("\n")[0])

        # Assert timing is reasonable (10-20ms for 10ms sleep + overhead)
        assert 8 <= event["timing_ms"] <= 30, f"Unrealistic timing {event['timing_ms']}ms"

class TestTelemetrySummary:
    """Test last_run.json aggregation."""

    def test_ast_summary_calculation(self, tmp_path):
        """Verify AST counters aggregated correctly."""
        telemetry = Telemetry(tmp_path, level="lite")

        telemetry.incr("ast_parse_count", 100)
        telemetry.incr("ast_cache_hit_count", 86)

        telemetry.flush()

        last_run_file = tmp_path / "_ctx" / "telemetry" / "last_run.json"
        last_run = json.loads(last_run_file.read_text())

        assert last_run["ast"]["ast_parse_count"] == 100
        assert last_run["ast"]["ast_cache_hit_count"] == 86
        assert abs(last_run["ast"]["ast_cache_hit_rate"] - 0.86) < 0.01

    def test_lsp_summary_calculation(self, tmp_path):
        """Verify LSP counters + timeout_rate aggregated correctly."""
        telemetry = Telemetry(tmp_path, level="lite")

        telemetry.incr("lsp_spawn_count", 5)
        telemetry.incr("lsp_rea
