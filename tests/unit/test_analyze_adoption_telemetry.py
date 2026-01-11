"""Unit tests for analyze_adoption_telemetry.py.

Tests cover bug-specific fixes (race condition, edge cases) and comprehensive
coverage of all analysis functions.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Import from worktree version
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / ".worktrees" / "wo0013-ast-adoption-observability"))

from eval.scripts.analyze_adoption_telemetry import (
    analyze_backend_distribution,
    analyze_cache_effectiveness,
    analyze_lock_contention,
    filter_events_by_days,
    scan_db_growth,
    CACHE_DIR_NAME,
    CACHE_SUBDIR_NAME,
    CACHE_DB_PATTERN,
    BYTES_TO_MB,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_events():
    """Sample telemetry events for testing."""
    return [
        {
            "ts": "2026-01-09T12:00:00Z",
            "cmd": "ast.symbols",
            "result": {"backend": "FileLockedAstCache", "status": "ok"},
        },
        {
            "ts": "2026-01-09T12:01:00Z",
            "cmd": "ast.cache.hit",
            "result": {"backend": "FileLockedAstCache"},
        },
        {
            "ts": "2026-01-09T12:02:00Z",
            "cmd": "ast.cache.miss",
            "result": {"backend": "FileLockedAstCache"},
        },
        {
            "ts": "2026-01-09T12:03:00Z",
            "cmd": "ast.symbols",
            "result": {"backend": "InMemoryLRUCache", "status": "ok"},
        },
        {
            "ts": "2026-01-09T12:04:00Z",
            "cmd": "ast.cache.lock_wait",
            "timing_ms": 15,
            "result": {"backend": "FileLockedAstCache"},
        },
        {
            "ts": "2026-01-09T12:05:00Z",
            "cmd": "ast.cache.lock_timeout",
            "result": {"backend": "FileLockedAstCache"},
        },
    ]


@pytest.fixture
def mock_segment_path(tmp_path):
    """Create a mock segment path with cache directory."""
    cache_dir = tmp_path / CACHE_DIR_NAME / CACHE_SUBDIR_NAME
    cache_dir.mkdir(parents=True)
    return tmp_path


# ============================================================================
# Bug-Specific Tests (CRITICAL fixes)
# ============================================================================

def test_scan_db_growth_handles_deleted_files(mock_segment_path, caplog):
    """Test race condition fix: Files deleted between glob() and stat()."""
    # Create mock db files
    cache_dir = mock_segment_path / CACHE_DIR_NAME / CACHE_SUBDIR_NAME
    db1 = cache_dir / "ast_cache_abc123.db"
    db2 = cache_dir / "ast_cache_def456.db"
    db1.write_text("data1")
    db2.write_text("data2")

    # Mock Path.stat() to raise FileNotFoundError for second file
    original_stat = Path.stat

    def mock_stat(self):
        if self.name == "ast_cache_def456.db":
            raise FileNotFoundError(f"File not found: {self}")
        return original_stat(self)

    with patch.object(Path, 'stat', mock_stat):
        result = scan_db_growth(mock_segment_path)

    # Should continue processing and return partial results
    assert result["db_exists"] is True
    assert result["file_count"] == 2  # Still counts all files from glob
    assert len(result["files"]) == 1  # But only one successfully processed
    assert result["files"][0]["name"] == "ast_cache_abc123.db"

    # Should log warning for deleted file
    assert any("deleted during scan" in record.message.lower() for record in caplog.records)


def test_scan_db_growth_empty_cache_dir(mock_segment_path):
    """Test edge case: Cache directory exists but no .db files."""
    result = scan_db_growth(mock_segment_path)

    assert result["db_exists"] is True
    assert result["file_count"] == 0
    assert result["total_size_mb"] == 0
    assert result["files"] == []


def test_scan_db_growth_cache_dir_not_exists(tmp_path):
    """Test edge case: Cache directory doesn't exist."""
    result = scan_db_growth(tmp_path)

    assert result["db_exists"] is False
    assert result["file_count"] == 0
    assert result["total_size_mb"] == 0
    assert result["files"] == []


def test_analyze_lock_contention_empty_events():
    """Test edge case: Empty events list for lock contention."""
    result = analyze_lock_contention([])

    assert result["lock_waits"]["total_waits"] == 0
    assert result["lock_waits"]["avg_wait_ms"] == 0
    assert result["lock_waits"]["p50_wait_ms"] == 0
    assert result["lock_waits"]["p95_wait_ms"] == 0
    assert result["lock_waits"]["max_wait_ms"] == 0
    assert result["timeouts"]["count"] == 0
    assert result["timeouts"]["rate_percent"] == 0


def test_analyze_lock_contention_single_wait():
    """Test edge case: Single lock wait event (percentile calculation)."""
    events = [
        {"cmd": "ast.cache.lock_wait", "timing_ms": 42}
    ]

    result = analyze_lock_contention(events)

    # With single value, all percentiles should equal that value
    assert result["lock_waits"]["total_waits"] == 1
    assert result["lock_waits"]["avg_wait_ms"] == 42
    assert result["lock_waits"]["p50_wait_ms"] == 42
    assert result["lock_waits"]["p95_wait_ms"] == 42
    assert result["lock_waits"]["max_wait_ms"] == 42


def test_constants_defined():
    """Test configuration validation: Constants are defined correctly."""
    assert CACHE_DIR_NAME == ".trifecta"
    assert CACHE_SUBDIR_NAME == "cache"
    assert CACHE_DB_PATTERN == "ast_cache_*.db"
    assert BYTES_TO_MB == 1024 * 1024


# ============================================================================
# Comprehensive Tests (All Analysis Functions)
# ============================================================================

def test_analyze_backend_distribution_empty_events():
    """Test edge case: Empty events for backend distribution."""
    result = analyze_backend_distribution([])

    assert result["total_runs"] == 0
    assert result["by_backend"] == {}
    # adoption_rate is NOT included when total_runs == 0
    assert "adoption_rate" not in result


def test_analyze_backend_distribution_counts_correctly(sample_events):
    """Test happy path: Backend distribution calculates correctly.

    Note: The function counts ALL events with result.backend field,
    not just ast.symbols commands.
    """
    result = analyze_backend_distribution(sample_events)

    # All 6 events have backend field
    assert result["total_runs"] == 6
    assert result["by_backend"]["FileLockedAstCache"]["count"] == 5
    assert result["by_backend"]["InMemoryLRUCache"]["count"] == 1
    assert result["by_backend"]["FileLockedAstCache"]["percentage"] == 83.3
    assert result["by_backend"]["InMemoryLRUCache"]["percentage"] == 16.7
    assert result["adoption_rate"] == 83.3


def test_analyze_backend_distribution_unknown_backend():
    """Test edge case: Events with missing backend field."""
    events = [
        {"cmd": "ast.symbols", "result": {"status": "ok"}},  # No backend
        {"cmd": "ast.symbols", "result": {"backend": "FileLockedAstCache"}},
    ]

    result = analyze_backend_distribution(events)

    assert result["total_runs"] == 2
    assert result["by_backend"]["Unknown"]["count"] == 1
    assert result["by_backend"]["FileLockedAstCache"]["count"] == 1


def test_analyze_cache_effectiveness_no_hits_misses():
    """Test edge case: No hit/miss events."""
    events = [
        {"cmd": "ast.symbols", "result": {"backend": "FileLockedAstCache"}},
        {"cmd": "ast.cache.write", "result": {"backend": "FileLockedAstCache"}},
    ]

    result = analyze_cache_effectiveness(events)

    # Should return empty dict when no hits/misses
    assert result == {}


def test_analyze_cache_effectiveness_calculates_hit_rate(sample_events):
    """Test happy path: Hit rate calculated correctly."""
    result = analyze_cache_effectiveness(sample_events)

    # FileLockedAstCache: 1 hit, 1 miss = 50% hit rate
    assert "FileLockedAstCache" in result
    assert result["FileLockedAstCache"]["hits"] == 1
    assert result["FileLockedAstCache"]["misses"] == 1
    assert result["FileLockedAstCache"]["total_operations"] == 2
    assert result["FileLockedAstCache"]["hit_rate"] == 0.5


def test_filter_events_by_days_filters_correctly():
    """Test time-based filtering."""
    now = datetime.now()
    old_event = (now - timedelta(days=10)).isoformat()
    recent_event = now.isoformat()

    events = [
        {"ts": old_event},
        {"ts": recent_event},
    ]

    # Filter for last 1 day (should only keep recent event)
    result = filter_events_by_days(events, days=1)

    assert len(result) == 1
    assert result[0]["ts"] == recent_event
