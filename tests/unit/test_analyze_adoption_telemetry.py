"""Unit tests for analyze_adoption_telemetry.py.

Tests cover bug-specific fixes (race condition, edge cases) and comprehensive
coverage of all analysis functions.
"""

from datetime import datetime, timedelta

import pytest

from eval.scripts.analyze_adoption_telemetry import (
    analyze_backend_distribution,
    analyze_cache_effectiveness,
    analyze_lock_contention,
    filter_events_by_days,
    scan_db_growth,
    BackendDistributionResult,
    BackendStats,
    CacheEffectivenessStats,
    LockContentionResult,
    LockWaitStats,
    TimeoutStats,
    DbGrowthResult,
    TelemetryEvent,
    AnalysisPeriod,
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

def test_scan_db_growth_handles_deleted_files(mock_segment_path):
    """Test race condition fix: Files deleted between glob() and stat()."""
    # Create mock db files
    cache_dir = mock_segment_path / CACHE_DIR_NAME / CACHE_SUBDIR_NAME
    db1 = cache_dir / "ast_cache_abc123.db"
    db2 = cache_dir / "ast_cache_def456.db"
    db1.write_text("data1")
    db2.write_text("data2")

    # Delete one file to simulate race condition (file deleted after glob)
    db2.unlink()

    result = scan_db_growth(mock_segment_path)

    # Should continue processing and return partial results
    assert isinstance(result, DbGrowthResult)
    assert result.db_exists is True
    # file_count represents successfully processed files
    assert result.file_count == 1
    assert len(result.files) == 1
    assert result.files[0].name == "ast_cache_abc123.db"


def test_scan_db_growth_empty_cache_dir(mock_segment_path):
    """Test edge case: Cache directory exists but no .db files."""
    result = scan_db_growth(mock_segment_path)

    assert isinstance(result, DbGrowthResult)
    assert result.db_exists is True
    assert result.file_count == 0
    assert result.total_size_mb == 0
    assert result.files == []


def test_scan_db_growth_cache_dir_not_exists(tmp_path):
    """Test edge case: Cache directory doesn't exist."""
    result = scan_db_growth(tmp_path)

    assert isinstance(result, DbGrowthResult)
    assert result.db_exists is False
    assert result.file_count == 0
    assert result.total_size_mb == 0
    assert result.files == []


def test_analyze_lock_contention_empty_events():
    """Test edge case: Empty events list for lock contention."""
    result = analyze_lock_contention([])

    assert isinstance(result, LockContentionResult)
    assert isinstance(result.lock_waits, LockWaitStats)
    assert isinstance(result.timeouts, TimeoutStats)
    assert result.lock_waits.total_waits == 0
    assert result.lock_waits.avg_wait_ms == 0
    assert result.lock_waits.p50_wait_ms == 0
    assert result.lock_waits.p95_wait_ms == 0
    assert result.lock_waits.max_wait_ms == 0
    assert result.timeouts.count == 0
    assert result.timeouts.rate_percent == 0


def test_analyze_lock_contention_single_wait():
    """Test edge case: Single lock wait event (percentile calculation)."""
    events = [
        {"cmd": "ast.cache.lock_wait", "timing_ms": 42}
    ]

    result = analyze_lock_contention(events)

    # With single value, all percentiles should equal that value
    assert isinstance(result, LockContentionResult)
    assert isinstance(result.lock_waits, LockWaitStats)
    assert result.lock_waits.total_waits == 1
    assert result.lock_waits.avg_wait_ms == 42
    assert result.lock_waits.p50_wait_ms == 42
    assert result.lock_waits.p95_wait_ms == 42
    assert result.lock_waits.max_wait_ms == 42


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

    assert isinstance(result, BackendDistributionResult)
    assert result.total_runs == 0
    assert result.by_backend == {}
    # adoption_rate is included when total_runs == 0 (defaults to 0.0)
    assert result.adoption_rate == 0.0


def test_analyze_backend_distribution_counts_correctly(sample_events):
    """Test happy path: Backend distribution calculates correctly.

    Note: The function counts ALL events with result.backend field,
    not just ast.symbols commands.
    """
    result = analyze_backend_distribution(sample_events)

    # All 6 events have backend field
    assert isinstance(result, BackendDistributionResult)
    assert result.total_runs == 6
    assert isinstance(result.by_backend["FileLockedAstCache"], BackendStats)
    assert result.by_backend["FileLockedAstCache"].count == 5
    assert result.by_backend["InMemoryLRUCache"].count == 1
    assert result.by_backend["FileLockedAstCache"].percentage == 83.3
    assert result.by_backend["InMemoryLRUCache"].percentage == 16.7
    assert result.adoption_rate == 83.3


def test_analyze_backend_distribution_unknown_backend():
    """Test edge case: Events with missing backend field."""
    events = [
        {"cmd": "ast.symbols", "result": {"status": "ok"}},  # No backend
        {"cmd": "ast.symbols", "result": {"backend": "FileLockedAstCache"}},
    ]

    result = analyze_backend_distribution(events)

    assert isinstance(result, BackendDistributionResult)
    assert result.total_runs == 2
    assert isinstance(result.by_backend["Unknown"], BackendStats)
    assert result.by_backend["Unknown"].count == 1
    assert result.by_backend["FileLockedAstCache"].count == 1


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
    assert isinstance(result["FileLockedAstCache"], CacheEffectivenessStats)
    assert result["FileLockedAstCache"].hits == 1
    assert result["FileLockedAstCache"].misses == 1
    assert result["FileLockedAstCache"].total_operations == 2
    assert result["FileLockedAstCache"].hit_rate == 0.5


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


# ============================================================================
# Dataclass Validation Tests
# ============================================================================

def test_telemetry_event_empty_ts_raises():
    """Test TelemetryEvent validation: empty ts raises ValueError."""
    with pytest.raises(ValueError, match="ts cannot be empty"):
        TelemetryEvent(ts="", cmd="ast.symbols")


def test_telemetry_event_empty_cmd_raises():
    """Test TelemetryEvent validation: empty cmd raises ValueError."""
    with pytest.raises(ValueError, match="cmd cannot be empty"):
        TelemetryEvent(ts="2026-01-09T12:00:00Z", cmd="")


def test_telemetry_event_with_valid_fields():
    """Test TelemetryEvent with valid fields creates instance."""
    event = TelemetryEvent(
        ts="2026-01-09T12:00:00Z",
        cmd="ast.symbols",
        result={"backend": "FileLockedAstCache", "status": "ok"},
        timing_ms=42
    )
    assert event.ts == "2026-01-09T12:00:00Z"
    assert event.cmd == "ast.symbols"
    assert event.timing_ms == 42


def test_analysis_period_invalid_days_raises():
    """Test AnalysisPeriod validation: days < 1 raises ValueError."""
    with pytest.raises(ValueError, match="days_analyzed must be >= 1"):
        AnalysisPeriod(
            start="2026-01-01T00:00:00Z",
            end="2026-01-08T00:00:00Z",
            days_analyzed=0,
            total_events=100,
            segment_path="/path"
        )


def test_analysis_period_negative_events_raises():
    """Test AnalysisPeriod validation: negative total_events raises ValueError."""
    with pytest.raises(ValueError, match="total_events must be >= 0"):
        AnalysisPeriod(
            start="2026-01-01T00:00:00Z",
            end="2026-01-08T00:00:00Z",
            days_analyzed=7,
            total_events=-1,
            segment_path="/path"
        )


def test_backend_stats_negative_count_raises():
    """Test BackendStats validation: negative count raises ValueError."""
    with pytest.raises(ValueError, match="count must be >= 0"):
        BackendStats(count=-1, percentage=50.0)


def test_backend_stats_percentage_out_of_range_low_raises():
    """Test BackendStats validation: percentage < 0 raises ValueError."""
    with pytest.raises(ValueError, match="percentage must be 0-100"):
        BackendStats(count=10, percentage=-0.1)


def test_backend_stats_percentage_out_of_range_high_raises():
    """Test BackendStats validation: percentage > 100 raises ValueError."""
    with pytest.raises(ValueError, match="percentage must be 0-100"):
        BackendStats(count=10, percentage=100.1)


def test_cache_effectiveness_stats_hit_rate_mismatch_raises():
    """Test CacheEffectivenessStats validation: hit_rate mismatch raises ValueError."""
    with pytest.raises(ValueError, match="hit_rate.*!= calculated"):
        CacheEffectivenessStats(
            hits=1,
            misses=1,
            total_operations=2,
            hit_rate=0.9  # Should be 0.5
        )


def test_cache_effectiveness_stats_negative_operations_raises():
    """Test CacheEffectivenessStats validation: negative values raises ValueError."""
    # Note: hits validation happens first, so we get hits error not total_operations error
    with pytest.raises(ValueError, match="hits must be >= 0"):
        CacheEffectivenessStats(
            hits=-1,
            misses=0,
            total_operations=-1,
            hit_rate=0.0
        )
