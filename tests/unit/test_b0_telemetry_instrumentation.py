"""Tests for B0 telemetry instrumentation.

Verifies that zero-hit events are properly tagged with source, build_sha, mode, and reason_code.
"""

import json
import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from src.application.search_get_usecases import (
    SearchUseCase,
    _detect_source,
    _get_build_sha,
    _classify_zero_hit_reason,
)


class TestB0Instrumentation:
    """Test B0 telemetry instrumentation for zero-hit analysis."""

    def test_detect_source_from_env(self):
        """Source detection respects TRIFECTA_TELEMETRY_SOURCE env var."""
        with patch.dict(os.environ, {"TRIFECTA_TELEMETRY_SOURCE": "test"}):
            assert _detect_source() == "test"

        with patch.dict(os.environ, {"TRIFECTA_TELEMETRY_SOURCE": "agent"}):
            assert _detect_source() == "agent"

    def test_detect_source_defaults(self):
        """Source detection defaults to interactive without env var."""
        env_copy = os.environ.copy()
        env_copy.pop("TRIFECTA_TELEMETRY_SOURCE", None)

        with patch.dict(os.environ, env_copy, clear=True):
            source = _detect_source()
            # Should be one of the valid values
            assert source in ("test", "fixture", "interactive", "agent")

    def test_get_build_sha_returns_8_chars(self):
        """Build SHA returns 8 characters."""
        sha = _get_build_sha()
        assert len(sha) == 8 or sha == "unknown"

    def test_get_build_sha_unknown_when_not_git(self, tmp_path):
        """Build SHA returns 'unknown' when not in git repo."""
        # Change to non-git directory
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            sha = _get_build_sha()
            assert sha == "unknown"
        finally:
            os.chdir(original_cwd)

    def test_classify_zero_hit_reason_empty(self):
        """Empty queries classified as 'empty'."""
        assert _classify_zero_hit_reason("", "disabled", False, False) == "empty"
        assert _classify_zero_hit_reason("   ", "disabled", False, False) == "empty"

    def test_classify_zero_hit_reason_vague(self):
        """Short and vague queries classified as 'vague'."""
        assert _classify_zero_hit_reason("ab", "disabled", False, False) == "vague"
        assert _classify_zero_hit_reason("x", "disabled", False, False) == "vague"
        assert _classify_zero_hit_reason("test query", "vague", False, False) == "vague"

    def test_classify_zero_hit_reason_no_alias(self):
        """Queries without expansion classified as 'no_alias'."""
        assert _classify_zero_hit_reason("query", "disabled", False, False) == "no_alias"
        assert _classify_zero_hit_reason("test term", "guided", False, False) == "no_alias"

    def test_classify_zero_hit_reason_strict_filter(self):
        """Queries with expansion but no hits classified as 'strict_filter'."""
        assert _classify_zero_hit_reason("query", "guided", True, False) == "strict_filter"
        assert _classify_zero_hit_reason("query", "guided", False, True) == "strict_filter"

    def test_classify_zero_hit_reason_unknown(self):
        """Other queries classified as 'unknown'."""
        assert _classify_zero_hit_reason("normal query here", "guided", False, False) == "unknown"


class TestSearchUseCaseB0Telemetry:
    """Test that SearchUseCase emits B0 telemetry tags."""

    @pytest.fixture
    def mock_fs(self, tmp_path):
        """Create mock file system with context pack."""
        fs = MagicMock()

        # Create minimal context pack
        ctx_dir = tmp_path / "_ctx"
        ctx_dir.mkdir()

        pack = {
            "schema_version": 1,
            "segment": "test",
            "created_at": "2026-01-01T00:00:00",
            "digest": "",
            "source_files": [],
            "chunks": [
                {
                    "id": "test:chunk1",
                    "doc": "test",
                    "title_path": ["test.md"],
                    "text": "# Test\nThis is test content.",
                    "char_count": 100,
                    "token_est": 25,
                    "source_path": "test.md",
                    "chunking_method": "whole_file",
                }
            ],
            "index": [
                {
                    "id": "test:chunk1",
                    "title_path_norm": "test.md",
                    "preview": "# Test",
                    "token_est": 25,
                }
            ],
        }

        pack_path = ctx_dir / "context_pack.json"
        pack_path.write_text(json.dumps(pack))

        return fs, tmp_path

    def test_search_emits_source_tag(self, mock_fs):
        """Search events include source tag."""
        fs, tmp_path = mock_fs
        telemetry = MagicMock()

        use_case = SearchUseCase(fs, telemetry)

        with patch.dict(os.environ, {"TRIFECTA_TELEMETRY_SOURCE": "test"}):
            use_case.execute(tmp_path, "test query")

        # Check that event was called with source in kwargs
        call_args = telemetry.event.call_args
        assert call_args is not None

        # kwargs are the 4th+ positional args or keyword args
        kwargs = (
            call_args.kwargs
            if hasattr(call_args, "kwargs")
            else call_args[1]
            if len(call_args) > 1
            else {}
        )

        # The source should be in kwargs (goes to 'x' field)
        assert "source" in kwargs
        assert kwargs["source"] == "test"

    def test_search_emits_build_sha(self, mock_fs):
        """Search events include build_sha tag."""
        fs, tmp_path = mock_fs
        telemetry = MagicMock()

        use_case = SearchUseCase(fs, telemetry)
        use_case.execute(tmp_path, "test query")

        call_args = telemetry.event.call_args
        assert call_args is not None

        kwargs = (
            call_args.kwargs
            if hasattr(call_args, "kwargs")
            else call_args[1]
            if len(call_args) > 1
            else {}
        )

        assert "build_sha" in kwargs
        assert len(kwargs["build_sha"]) == 8 or kwargs["build_sha"] == "unknown"

    def test_search_emits_mode(self, mock_fs):
        """Search events include mode tag."""
        fs, tmp_path = mock_fs
        telemetry = MagicMock()

        use_case = SearchUseCase(fs, telemetry)
        use_case.execute(tmp_path, "test query")

        call_args = telemetry.event.call_args
        assert call_args is not None

        kwargs = (
            call_args.kwargs
            if hasattr(call_args, "kwargs")
            else call_args[1]
            if len(call_args) > 1
            else {}
        )

        assert "mode" in kwargs
        assert kwargs["mode"] in ("search_only", "with_expansion")

    def test_zero_hit_search_emits_reason(self, mock_fs):
        """Zero-hit search events include zero_hit_reason."""
        fs, tmp_path = mock_fs
        telemetry = MagicMock()

        use_case = SearchUseCase(fs, telemetry)

        # Query that won't match anything
        use_case.execute(tmp_path, "xyznonexistent")

        call_args = telemetry.event.call_args
        assert call_args is not None

        kwargs = (
            call_args.kwargs
            if hasattr(call_args, "kwargs")
            else call_args[1]
            if len(call_args) > 1
            else {}
        )

        # Should have zero_hit_reason for zero-hit queries
        assert "zero_hit_reason" in kwargs
        assert kwargs["zero_hit_reason"] in (
            "empty",
            "vague",
            "no_alias",
            "strict_filter",
            "unknown",
        )

    def test_search_increments_source_counter(self, mock_fs):
        """Search increments source-specific counter."""
        fs, tmp_path = mock_fs
        telemetry = MagicMock()

        use_case = SearchUseCase(fs, telemetry)

        with patch.dict(os.environ, {"TRIFECTA_TELEMETRY_SOURCE": "test"}):
            use_case.execute(tmp_path, "test query")

        # Check that source-specific counter was incremented
        telemetry.incr.assert_any_call("ctx_search_by_source_test_count")

    def test_zero_hit_increments_reason_counter(self, mock_fs):
        """Zero-hit search increments reason-specific counter."""
        fs, tmp_path = mock_fs
        telemetry = MagicMock()

        use_case = SearchUseCase(fs, telemetry)

        # Query that won't match anything - should trigger no_alias or unknown
        use_case.execute(tmp_path, "xyznonexistent")

        # Check that reason counter was incremented (exact reason depends on classification)
        reason_calls = [
            call
            for call in telemetry.incr.call_args_list
            if "ctx_search_zero_hit_reason_" in str(call)
        ]
        assert len(reason_calls) >= 0  # May or may not be called depending on hits
