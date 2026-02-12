"""Unit tests for telemetry_rotate script.

TDD approach: Tests written first (RED), then implementation (GREEN).
"""

from pathlib import Path
import sys

import pytest

# Add scripts to path for import
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from src.domain.result import Ok, Err


class TestGetTelemetryDir:
    """Test get_telemetry_dir function."""

    def test_uses_env_var_when_set(self, monkeypatch, tmp_path):
        """Should use TRIFECTA_TELEMETRY_DIR env var when set."""
        monkeypatch.setenv("TRIFECTA_TELEMETRY_DIR", str(tmp_path))
        from telemetry_rotate import get_telemetry_dir

        result = get_telemetry_dir()
        assert result == tmp_path

    def test_falls_back_to_default_when_env_not_set(self, monkeypatch):
        """Should use _ctx/telemetry when env var not set."""
        monkeypatch.delenv("TRIFECTA_TELEMETRY_DIR", raising=False)
        from telemetry_rotate import get_telemetry_dir

        result = get_telemetry_dir()
        assert result.name == "telemetry"
        assert result.parent.name == "_ctx"


class TestCountEvents:
    """Test count_events function."""

    def test_returns_zero_for_nonexistent_file(self, tmp_path):
        """Should return Ok(0) for nonexistent file."""
        from telemetry_rotate import count_events

        result = count_events(tmp_path / "nonexistent.jsonl")
        assert isinstance(result, Ok)
        assert result.unwrap() == 0

    def test_counts_newline_delimited_events(self, tmp_path):
        """Should count JSONL lines correctly."""
        events_file = tmp_path / "events.jsonl"
        events_file.write_text('{"event":1}\n{"event":2}\n')

        from telemetry_rotate import count_events

        result = count_events(events_file)
        assert isinstance(result, Ok)
        assert result.unwrap() == 2

    def test_handles_empty_file(self, tmp_path):
        """Should return Ok(0) for empty file."""
        events_file = tmp_path / "events.jsonl"
        events_file.write_text("")

        from telemetry_rotate import count_events

        result = count_events(events_file)
        assert isinstance(result, Ok)
        assert result.unwrap() == 0

    def test_returns_err_on_permission_denied(self, tmp_path):
        """Should return Err on PermissionError."""
        events_file = tmp_path / "events.jsonl"
        events_file.write_text('{"test": "data"}\n')
        events_file.chmod(0o000)

        from telemetry_rotate import count_events

        result = count_events(events_file)
        assert isinstance(result, Err)
        assert "Permission denied" in result.unwrap_err()

    def test_handles_windows_line_endings(self, tmp_path):
        """Should count lines with \\r\\n correctly."""
        events_file = tmp_path / "events.jsonl"
        events_file.write_text('{"event":1}\r\n{"event":2}\r\n')

        from telemetry_rotate import count_events

        result = count_events(events_file)
        assert isinstance(result, Ok)
        assert result.unwrap() == 2


class TestGetSizeMb:
    """Test get_size_mb function."""

    def test_returns_zero_for_nonexistent_file(self, tmp_path):
        """Should return Ok(0.0) for nonexistent file."""
        from telemetry_rotate import get_size_mb

        result = get_size_mb(tmp_path / "nonexistent.jsonl")
        assert isinstance(result, Ok)
        assert result.unwrap() == 0.0

    def test_calculates_size_in_megabytes(self, tmp_path):
        """Should calculate size correctly in MB."""
        events_file = tmp_path / "events.jsonl"
        events_file.write_text("x" * (1024 * 1024))  # 1 MB

        from telemetry_rotate import get_size_mb

        result = get_size_mb(events_file)
        assert isinstance(result, Ok)
        assert result.unwrap() == pytest.approx(1.0, rel=0.1)


class TestRotateEvents:
    """Test rotate_events function."""

    def test_noop_for_nonexistent_file(self, tmp_path, capsys):
        """Should return Err for nonexistent file."""
        from telemetry_rotate import rotate_events

        result = rotate_events(tmp_path / "nonexistent.jsonl")
        _ = capsys.readouterr()
        assert isinstance(result, Err)

    def test_creates_rotated_file_with_expected_naming(self, tmp_path):
        """Should create rotated file with correct naming format."""
        events_file = tmp_path / "events.jsonl"
        events_file.write_text('{"test": "data"}\n')

        from telemetry_rotate import rotate_events

        result = rotate_events(events_file)

        # Should return Ok with RotationResult
        assert isinstance(result, Ok)
        rotated = result.unwrap()
        assert ".jsonl.rotated" in str(rotated.to_path)
        assert rotated.to_path.suffix == ".rotated"

    def test_handles_unicode_in_events_file(self, tmp_path):
        """Should handle unicode content correctly."""
        events_file = tmp_path / "events.jsonl"
        events_file.write_text('{"message": "Hello 世界"}\n')

        from telemetry_rotate import rotate_events

        result = rotate_events(events_file)
        assert isinstance(result, Ok)

        rotated = result.unwrap().to_path
        content = rotated.read_text(encoding="utf-8")
        assert "Hello 世界" in content


class TestBoundaryConditions:
    """Test threshold boundary conditions."""

    def test_exactly_max_events_triggers_rotation(self, tmp_path):
        """Should rotate when exactly at MAX_EVENTS threshold."""
        from telemetry_rotate import MAX_EVENTS, count_events

        events_file = tmp_path / "events.jsonl"
        events_file.write_text("\n".join([f'{{"event":{i}}}' for i in range(MAX_EVENTS)]))

        result = count_events(events_file)
        assert isinstance(result, Ok)
        count = result.unwrap()
        should_rotate = count >= MAX_EVENTS
        assert should_rotate is True

    def test_one_below_max_events_no_rotation(self, tmp_path):
        """Should NOT rotate when one below MAX_EVENTS."""
        from telemetry_rotate import MAX_EVENTS, count_events

        events_file = tmp_path / "events.jsonl"
        events_file.write_text("\n".join([f'{{"event":{i}}}' for i in range(MAX_EVENTS - 1)]))

        result = count_events(events_file)
        assert isinstance(result, Ok)
        count = result.unwrap()
        should_rotate = count >= MAX_EVENTS
        assert should_rotate is False
