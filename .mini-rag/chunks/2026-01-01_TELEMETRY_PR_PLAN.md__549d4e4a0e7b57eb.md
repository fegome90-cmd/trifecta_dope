= tmp_path / "_ctx" / "telemetry" / "events.jsonl"
        events = [json.loads(line) for line in events_file.read_text().strip().split("\n") if line]

        # Should have at least some events (may drop due to lock, but structure is valid)
        assert len(events) > 0

        # All events should be valid JSON
        for event in events:
            assert "cmd" in event
            assert "timing_ms" in event
```
