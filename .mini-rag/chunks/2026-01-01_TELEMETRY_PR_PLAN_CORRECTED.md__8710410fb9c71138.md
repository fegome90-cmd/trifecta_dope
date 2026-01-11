y.event(
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

    def test_relpath_inside_workspace(self):
        """Verify relative path for files inside workspace."""
        root = Path("/workspaces/trifecta_dope")
        target = Path("/workspaces/trifecta_dope/src/domain/models.py")

        result = _relpath(root, target)

        assert result == "src/domain/models.py"
        assert not result.startswith("/")

    def test_relpath_outside_workspace(self):
        """Verify external/<hash>-<name> for files outside workspace."""
        root = Path("/workspaces/trifecta_dope")
        target = Path("/usr/lib/python3.12/typing.py")

        result = _relpath(root, target)

        assert result.startswith("external/")
        assert result.endswith("-typing.py")
        assert "/" not in result.split("-", 1)[1]  # No slashes after has
