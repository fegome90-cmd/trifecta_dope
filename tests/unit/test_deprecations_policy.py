"""Unit tests for deprecated code path tracking policy.

Tests the maybe_emit_deprecated helper with different TRIFECTA_DEPRECATED policies.
"""

import pytest
from unittest.mock import Mock
from src.infrastructure.deprecations import maybe_emit_deprecated


def test_deprecated_policy_off_no_emission(monkeypatch):
    """With policy=off, should not emit telemetry event."""
    monkeypatch.setenv("TRIFECTA_DEPRECATED", "off")

    mock_telemetry = Mock()

    # Should return without calling telemetry
    maybe_emit_deprecated("test_deprecated_id", mock_telemetry)

    mock_telemetry.event.assert_not_called()


def test_deprecated_policy_warn_emits_event(monkeypatch):
    """With policy=warn, should emit telemetry event only."""
    monkeypatch.setenv("TRIFECTA_DEPRECATED", "warn")

    mock_telemetry = Mock()

    # Should emit event but not exit
    maybe_emit_deprecated("test_deprecated_id", mock_telemetry)

    # Verify event was emitted with correct structure
    mock_telemetry.event.assert_called_once_with(
        "deprecated.used",
        {"id": "test_deprecated_id"},
        {},
        0,
    )


def test_deprecated_policy_fail_emits_and_exits(monkeypatch):
    """With policy=fail, should emit event and exit with code 2."""
    monkeypatch.setenv("TRIFECTA_DEPRECATED", "fail")

    mock_telemetry = Mock()

    # Should emit event and then raise SystemExit(2)
    with pytest.raises(SystemExit) as exc_info:
        maybe_emit_deprecated("test_deprecated_id", mock_telemetry)

    # Verify exit code
    assert exc_info.value.code == 2

    # Verify event was emitted before exit
    mock_telemetry.event.assert_called_once_with(
        "deprecated.used",
        {"id": "test_deprecated_id"},
        {},
        0,
    )


def test_deprecated_default_policy_is_off(monkeypatch):
    """Without TRIFECTA_DEPRECATED env var, default should be 'off'."""
    # Ensure env var is not set
    monkeypatch.delenv("TRIFECTA_DEPRECATED", raising=False)

    mock_telemetry = Mock()

    # Should not emit (default is off)
    maybe_emit_deprecated("test_deprecated_id", mock_telemetry)

    mock_telemetry.event.assert_not_called()


def test_deprecated_invalid_policy_treated_as_warn(monkeypatch):
    """Invalid policy values should be treated as 'warn' (emit event)."""
    monkeypatch.setenv("TRIFECTA_DEPRECATED", "invalid_value")

    mock_telemetry = Mock()

    # Should emit event (invalid values treated as warn, not off)
    maybe_emit_deprecated("test_deprecated_id", mock_telemetry)

    # Verify event was emitted
    mock_telemetry.event.assert_called_once()
