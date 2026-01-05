assert "/" not in result.split("-", 1)[1]  # No slashes after hash

    def test_relpath_uniqueness(self):
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

    def test_extra_fields_in_event(self, tmp_path):
        """Verify extra fields appear in events.jsonl."""
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
        assert event["
