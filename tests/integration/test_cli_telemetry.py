"""Integration tests for CLI telemetry events.

Tests that invalid_option_handler emits telemetry events correctly.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from src.cli.invalid_option_handler import (
    emit_help_used_telemetry,
    get_telemetry_kpis,
    handle_invalid_option_error,
    reset_introspector,
    reset_telemetry,
)


@pytest.fixture(autouse=True)
def reset_telemetry_state():
    """Reset telemetry state before each test."""
    reset_telemetry()
    reset_introspector()
    yield
    reset_telemetry()
    reset_introspector()


@pytest.fixture
def telemetry_dir():
    """Create a temporary directory for telemetry."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["TRIFECTA_TELEMETRY_DIR"] = tmpdir
        # Create the telemetry directory
        telemetry_path = Path(tmpdir)
        telemetry_path.mkdir(parents=True, exist_ok=True)
        yield telemetry_path
        # Cleanup
        if "TRIFECTA_TELEMETRY_DIR" in os.environ:
            del os.environ["TRIFECTA_TELEMETRY_DIR"]


class TestInvalidOptionTelemetry:
    """Tests for invalid_option telemetry events."""

    def test_emits_invalid_option_event(self, telemetry_dir):
        """Test that invalid_option event is emitted."""
        argv = ["trifecta", "load", "--segment", ".", "--task", "test", "--dry-run"]
        error_msg = "No such option: --dry-run"

        # Handle the error
        result = handle_invalid_option_error(error_msg, argv)

        # Verify error message is enhanced (accept both Unicode and ASCII fallback)
        assert ("❌ Error: No such option: --dry-run" in result or
                "[ERROR] Error: No such option: --dry-run" in result)

        # Verify telemetry event was written
        events_file = telemetry_dir / "events.jsonl"
        assert events_file.exists()

        with open(events_file) as f:
            events = [json.loads(line) for line in f]

        # Find the invalid_option event
        invalid_option_events = [e for e in events if e.get("cmd") == "invalid_option"]
        assert len(invalid_option_events) > 0

        event = invalid_option_events[0]
        assert event["args"]["command_path"] == "trifecta load"
        assert event["args"]["invalid_flag"] == "--dry-run"
        assert event["args"]["argv_len"] == len(argv)
        assert "result" in event
        assert "suggestions_count" in event["result"]
        assert "help_suggested" in event["result"]
        assert "had_match" in event["result"]
        # platform and is_tty are in "x" (kwargs)
        assert "x" in event
        assert "platform" in event["x"]
        assert "is_tty" in event["x"]

    def test_increments_invalid_option_count(self, telemetry_dir):
        """Test that invalid_option_count KPI is incremented."""
        argv = ["trifecta", "load", "--segment", ".", "--task", "test", "--dry-run"]
        error_msg = "No such option: --dry-run"

        # Handle the error twice
        handle_invalid_option_error(error_msg, argv)
        handle_invalid_option_error(error_msg, argv)

        # Check KPIs
        kpis = get_telemetry_kpis()
        assert kpis["invalid_option_count"] >= 2

    def test_emits_help_suggested_flag(self, telemetry_dir):
        """Test that help_suggested flag is set correctly."""
        argv = ["trifecta", "load", "--segment", ".", "--task", "test", "--hepl"]
        error_msg = "No such option: --hepl"

        # Handle the error (should suggest --help)
        result = handle_invalid_option_error(error_msg, argv)

        # Verify --help is suggested
        assert "--help" in result

        # Verify telemetry event
        events_file = telemetry_dir / "events.jsonl"
        with open(events_file) as f:
            events = [json.loads(line) for line in f]

        invalid_option_events = [e for e in events if e.get("cmd") == "invalid_option"]
        assert len(invalid_option_events) > 0

        event = invalid_option_events[0]
        assert event["result"]["help_suggested"] is True

    def test_no_event_for_unparseable_error(self, telemetry_dir):
        """Test that no event is emitted for unparseable errors."""
        argv = ["trifecta", "load"]
        error_msg = "Some other error"

        # Handle the error
        result = handle_invalid_option_error(error_msg, argv)

        # Should return original message
        assert result == error_msg

        # Verify no invalid_option event was written
        events_file = telemetry_dir / "events.jsonl"
        if events_file.exists():
            with open(events_file) as f:
                events = [json.loads(line) for line in f]
            invalid_option_events = [e for e in events if e.get("cmd") == "invalid_option"]
            assert len(invalid_option_events) == 0


class TestHelpUsedTelemetry:
    """Tests for help_used telemetry events."""

    def test_emits_help_used_event(self, telemetry_dir):
        """Test that help_used event is emitted."""
        argv = ["trifecta", "load", "--help"]
        command_path = "trifecta load"

        # Emit help used event
        emit_help_used_telemetry(command_path, argv)

        # Verify telemetry event was written
        events_file = telemetry_dir / "events.jsonl"
        assert events_file.exists()

        with open(events_file) as f:
            events = [json.loads(line) for line in f]

        # Find the help_used event
        help_events = [e for e in events if e.get("cmd") == "help_used"]
        assert len(help_events) > 0

        event = help_events[0]
        assert event["args"]["command_path"] == command_path
        assert event["args"]["argv_len"] == len(argv)
        # platform and is_tty are in "x" (kwargs)
        assert "x" in event
        assert "platform" in event["x"]
        assert "is_tty" in event["x"]

    def test_increments_help_used_count(self, telemetry_dir):
        """Test that help_used_count KPI is incremented."""
        argv = ["trifecta", "load", "--help"]
        command_path = "trifecta load"

        # Emit help used event twice
        emit_help_used_telemetry(command_path, argv)
        emit_help_used_telemetry(command_path, argv)

        # Check KPIs
        kpis = get_telemetry_kpis()
        assert kpis["help_used_count"] >= 2


class TestTelemetryKPIs:
    """Tests for telemetry KPI retrieval."""

    def test_get_telemetry_kpis_returns_dict(self, telemetry_dir):
        """Test that get_telemetry_kpis returns a dict with expected keys."""
        kpis = get_telemetry_kpis()

        assert isinstance(kpis, dict)
        assert "invalid_option_count" in kpis
        assert "help_used_count" in kpis
        assert isinstance(kpis["invalid_option_count"], int)
        assert isinstance(kpis["help_used_count"], int)

    def test_kpis_start_at_zero(self, telemetry_dir):
        """Test that KPIs start at zero after reset."""
        kpis = get_telemetry_kpis()
        assert kpis["invalid_option_count"] == 0
        assert kpis["help_used_count"] == 0
