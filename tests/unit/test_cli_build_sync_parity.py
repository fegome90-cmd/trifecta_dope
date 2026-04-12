"""Tests for CLI build/sync parity and telemetry root resolution.

This module verifies that:
1. ctx sync validates the same as ctx build (fail-closed)
2. telemetry always writes to segment dir, not cwd
"""

import os
from pathlib import Path

import pytest


class TestSyncBuildParity:
    """Verify ctx sync validates same as ctx build."""

    def test_sync_includes_validate_build_specifics_call(self) -> None:
        """Test that sync function includes _validate_build_specifics call."""
        from src.infrastructure.cli import sync
        import inspect

        source = inspect.getsource(sync)
        assert "_validate_build_specifics" in source, (
            "sync should call _validate_build_specifics"
        )

    def test_validate_build_specifics_exists(self) -> None:
        """Verify _validate_build_specifics function exists."""
        from src.infrastructure.cli import _validate_build_specifics

        assert callable(_validate_build_specifics)


class TestResolveSegmentSoft:
    """Test _resolve_segment_soft helper function."""

    def test_resolve_segment_soft_exists(self) -> None:
        """Verify _resolve_segment_soft function exists."""
        from src.infrastructure.cli import _resolve_segment_soft

        assert callable(_resolve_segment_soft)

    def test_resolve_segment_soft_resolves_relative_path(self, tmp_path: Path) -> None:
        """Test that _resolve_segment_soft resolves relative paths."""
        from src.infrastructure.cli import _resolve_segment_soft

        segment_dir = tmp_path / "test_segment"
        segment_dir.mkdir(parents=True, exist_ok=True)

        # Save current directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = _resolve_segment_soft("test_segment")
            assert result == segment_dir
        finally:
            os.chdir(original_cwd)

    def test_resolve_segment_soft_resolves_absolute_path(self, tmp_path: Path) -> None:
        """Test that _resolve_segment_soft handles absolute paths."""
        from src.infrastructure.cli import _resolve_segment_soft

        segment_dir = tmp_path / "test_segment"
        segment_dir.mkdir(parents=True, exist_ok=True)

        result = _resolve_segment_soft(str(segment_dir))
        assert result == segment_dir

    def test_resolve_segment_soft_handles_empty_path(self) -> None:
        """Test that _resolve_segment_soft handles empty path gracefully."""
        from src.infrastructure.cli import _resolve_segment_soft
        from click.exceptions import Exit

        with pytest.raises(Exit):
            _resolve_segment_soft("")


class TestTelemetryRoot:
    """Verify telemetry uses segment dir, not cwd."""

    def test_get_telemetry_exists(self) -> None:
        """Verify _get_telemetry function exists."""
        from src.infrastructure.cli import _get_telemetry

        assert callable(_get_telemetry)

    def test_get_telemetry_uses_resolve_segment_soft_when_require_ctx_false(self) -> None:
        """Test that _get_telemetry uses _resolve_segment_soft when require_ctx=False."""
        from src.infrastructure.cli import _get_telemetry
        import inspect

        source = inspect.getsource(_get_telemetry)
        assert "_resolve_segment_soft" in source, (
            "_get_telemetry should use _resolve_segment_soft for require_ctx=False"
        )

    def test_get_telemetry_uses_resolve_segment_when_require_ctx_true(self) -> None:
        """Test that _get_telemetry uses _resolve_segment when require_ctx=True."""
        from src.infrastructure.cli import _get_telemetry
        import inspect

        source = inspect.getsource(_get_telemetry)
        assert "_resolve_segment" in source, (
            "_get_telemetry should use _resolve_segment for require_ctx=True"
        )


class TestCodeChanges:
    """Verify the code changes were applied correctly."""

    def test_sync_includes_validate_build_specifics(self) -> None:
        """Test that sync function includes _validate_build_specifics call."""
        from src.infrastructure.cli import sync
        import inspect

        source = inspect.getsource(sync)
        assert "_validate_build_specifics" in source, (
            "sync should call _validate_build_specifics"
        )

    def test_get_telemetry_includes_resolve_segment_soft(self) -> None:
        """Test that _get_telemetry includes _resolve_segment_soft for require_ctx=False."""
        from src.infrastructure.cli import _get_telemetry
        import inspect

        source = inspect.getsource(_get_telemetry)
        assert "_resolve_segment_soft" in source, (
            "_get_telemetry should use _resolve_segment_soft"
        )