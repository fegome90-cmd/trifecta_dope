sert event["x"]["disclosure_mode"] == "excerpt"
        assert event["x"]["cache_hit"] is True

    def test_extra_fields_types(self, tmp_path):
        """Verify various types serialize correctly."""
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

    def test_ast_summary(self, tmp_path):
        """Verify AST summary calculation."""
        telemetry = Telemetry(tmp_path, level="lite")

        telemetry.incr("ast_parse_count", 100)
        telemetry.incr("ast_cache_hit_count", 86)
        te
