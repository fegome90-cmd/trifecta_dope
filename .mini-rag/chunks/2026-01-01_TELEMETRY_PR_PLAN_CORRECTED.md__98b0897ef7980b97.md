ncurrencySafety:
    """Test concurrent event logging (corruption-free guarantee)."""

    def test_concurrent_writes_no_corruption(self, tmp_path):
        """Verify concurrent writes produce valid JSON (no interleaved data)."""
        import threading

        def write_events(thread_id: int):
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
        assert len(events) <= 50, "A
