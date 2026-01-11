test(): pass"

        # First parse: cache miss
        builder.parse_python(code, Path("test.py"))

        # Second parse same file: cache hit (if implemented)
        # (This test will verify once caching is implemented)

        telemetry.flush()

        # Verify counter incremented
        last_run_file = tmp_path / "_ctx" / "telemetry" / "last_run.json"
        last_run = json.loads(last_run_file.read_text())

        assert last_run["metrics_delta"]["ast_parse_count"] >= 1

class TestConcurrentTelemetry:
    """Test concurrent command execution doesn't corrupt logs."""

    def test_concurrent_commands_no_corruption(self, tmp_path):
        """Spawn multiple commands, verify no event loss or corruption."""
        import threading

        def run_command(cmd_id: int):
            telemetry = Telemetry(tmp_path, level="lite")
            for i in range(5):
                telemetry.event(
                    f"cmd_{cmd_id}",
                    {"iteration": i},
                    {"status": "ok"},
                    10,
                )
            telemetry.flush()

        threads = [threading.Thread(target=run_command, args=(i,)) for i in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify events logged
        events_file = tmp_path / "_ctx" / "telemetry" / "events.jsonl"
        events = [j
