"""Tests for B2 intervention: Empty query pre-checks."""

import json
from pathlib import Path
from unittest.mock import MagicMock
import pytest

from src.application.search_get_usecases import SearchUseCase
from src.application.query_normalizer import QueryNormalizer


class TestB2EmptyQueryPreChecks:
    """Test B2 intervention: Early validation prevents zero-hit searches."""

    def test_validate_rejects_empty_string(self):
        """Empty string queries are rejected."""
        is_valid, error = QueryNormalizer.validate("")
        assert not is_valid
        assert "empty" in error.lower()

    def test_validate_rejects_whitespace_only(self):
        """Whitespace-only queries are rejected."""
        is_valid, error = QueryNormalizer.validate("   ")
        assert not is_valid
        assert "empty" in error.lower() or "whitespace" in error.lower()

        is_valid, error = QueryNormalizer.validate("\t\n  ")
        assert not is_valid

    def test_validate_rejects_single_char(self):
        """Single character queries are rejected."""
        is_valid, error = QueryNormalizer.validate("a")
        assert not is_valid
        assert "2 characters" in error.lower()

    def test_validate_accepts_valid_query(self):
        """Valid queries pass validation."""
        is_valid, error = QueryNormalizer.validate("test query")
        assert is_valid
        assert error == ""

    def test_validate_accepts_two_chars(self):
        """Two character queries pass validation."""
        is_valid, error = QueryNormalizer.validate("ab")
        assert is_valid
        assert error == ""

    def test_validate_rejects_none(self):
        """None queries are rejected."""
        is_valid, error = QueryNormalizer.validate(None)
        assert not is_valid
        assert "None" in error

    def test_validate_rejects_non_string(self):
        """Non-string queries are rejected."""
        is_valid, error = QueryNormalizer.validate(123)
        assert not is_valid
        assert "string" in error.lower()

    def test_search_rejects_empty_query_with_telemetry(self, tmp_path):
        """Search rejects empty query and emits telemetry."""
        fs = MagicMock()
        telemetry = MagicMock()

        use_case = SearchUseCase(fs, telemetry)
        result = use_case.execute(tmp_path, "")

        # Should return rejection message
        assert "rejected" in result.lower() or "Query rejected" in result

        # Should emit telemetry
        telemetry.incr.assert_called_with("ctx_search_rejected_invalid_query_count")
        telemetry.event.assert_called_once()

        # Verify event details
        call_args = telemetry.event.call_args
        assert call_args[0][0] == "ctx.search.rejected"
        # call_args[0] = (cmd, args, result, timing_ms)
        assert call_args[0][2]["rejected"] is True

    def test_search_rejects_whitespace_query(self, tmp_path):
        """Search rejects whitespace-only query."""
        fs = MagicMock()
        telemetry = MagicMock()

        use_case = SearchUseCase(fs, telemetry)
        result = use_case.execute(tmp_path, "   ")

        assert "rejected" in result.lower() or "Query rejected" in result
        telemetry.incr.assert_called_with("ctx_search_rejected_invalid_query_count")

    def test_search_rejects_single_char(self, tmp_path):
        """Search rejects single character query."""
        fs = MagicMock()
        telemetry = MagicMock()

        use_case = SearchUseCase(fs, telemetry)
        result = use_case.execute(tmp_path, "x")

        assert "rejected" in result.lower() or "Query rejected" in result

    def test_search_accepts_valid_query(self, tmp_path):
        """Search accepts valid queries normally."""
        fs = MagicMock()
        telemetry = MagicMock()

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
                    "text": "# Test\nContent here.",
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
        (ctx_dir / "context_pack.json").write_text(json.dumps(pack))

        use_case = SearchUseCase(fs, telemetry)
        result = use_case.execute(tmp_path, "test")

        # Should NOT be rejected
        assert "rejected" not in result.lower()
        # Should have searched (may find 0 hits, but not rejected)
        telemetry.event.assert_called_once()
        call_args = telemetry.event.call_args
        assert call_args[0][0] == "ctx.search"  # Normal search, not rejected


class TestB2Metrics:
    """Test B2 intervention metrics."""

    def test_rejection_increments_counter(self, tmp_path):
        """Rejection increments specific counter."""
        fs = MagicMock()
        telemetry = MagicMock()

        use_case = SearchUseCase(fs, telemetry)
        use_case.execute(tmp_path, "")

        # Verify specific counter was incremented
        calls = telemetry.incr.call_args_list
        rejection_calls = [c for c in calls if "rejected_invalid_query" in str(c)]
        assert len(rejection_calls) == 1

    def test_rejection_event_has_rejection_reason(self, tmp_path):
        """Rejection event includes reason."""
        fs = MagicMock()
        telemetry = MagicMock()

        use_case = SearchUseCase(fs, telemetry)
        use_case.execute(tmp_path, "")

        call_args = telemetry.event.call_args
        kwargs = (
            call_args.kwargs
            if hasattr(call_args, "kwargs")
            else call_args[1]
            if len(call_args) > 1
            else {}
        )

        # Should have rejection_reason in kwargs (goes to 'x' field)
        assert "rejection_reason" in kwargs
        assert "empty" in kwargs["rejection_reason"].lower()
