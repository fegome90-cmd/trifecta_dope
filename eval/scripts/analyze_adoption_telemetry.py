#!/usr/bin/env python3
"""Analyze AST cache adoption metrics from telemetry events.

Usage:
    python eval/scripts/analyze_adoption_telemetry.py --segment . --days 7 --out _ctx/metrics/wo0013_adoption.json
"""

import argparse
import json
import logging
import sys
from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, TypedDict


# Constants for cache analysis
CACHE_DIR_NAME = ".trifecta"
CACHE_SUBDIR_NAME = "cache"
CACHE_DB_PATTERN = "ast_cache_*.db"
BYTES_TO_MB = 1024 * 1024  # Bytes to Megabytes conversion factor


# ============================================================================
# Dataclasses for Type Safety
# ============================================================================


class TelemetryResult(TypedDict, total=False):
    """TypedDict for telemetry event result field.

    Uses total=False to make all fields optional, as different commands
    may return different result fields.
    """
    backend: str
    status: str


@dataclass(frozen=True, slots=True)
class TelemetryEvent:
    """A single telemetry event from events.jsonl.

    Invariants:
        - ts: ISO 8601 timestamp string
        - cmd: Command name (e.g., "ast.cache.hit")
        - result: Optional result dict with backend field
        - timing_ms: Optional timing in milliseconds
    """

    ts: str
    cmd: str
    result: TelemetryResult | None = None
    timing_ms: int | None = None

    def __post_init__(self) -> None:
        """Validate telemetry event invariants."""
        if not self.ts:
            raise ValueError("TelemetryEvent.ts cannot be empty")
        if not self.cmd:
            raise ValueError("TelemetryEvent.cmd cannot be empty")


@dataclass(frozen=True, slots=True)
class BackendStats:
    """Statistics for a single cache backend.

    Invariants:
        - count: Must be >= 0
        - percentage: Must be 0-100
    """

    count: int
    percentage: float

    def __post_init__(self) -> None:
        """Validate backend statistics invariants."""
        if self.count < 0:
            raise ValueError(f"BackendStats.count must be >= 0, got {self.count}")
        if not (0 <= self.percentage <= 100):
            raise ValueError(
                f"BackendStats.percentage must be 0-100, got {self.percentage}"
            )


@dataclass(frozen=True, slots=True)
class BackendDistributionResult:
    """Result of backend distribution analysis.

    Invariants:
        - total_runs: Must equal sum of all backend counts
        - adoption_rate: FileLockedAstCache adoption percentage (0-100)
    """

    total_runs: int
    by_backend: dict[str, BackendStats]
    adoption_rate: float | None = None

    def __post_init__(self) -> None:
        """Validate backend distribution invariants."""
        if self.total_runs < 0:
            raise ValueError(
                f"BackendDistributionResult.total_runs must be >= 0, got {self.total_runs}"
            )
        # Verify total_runs equals sum of counts
        sum_counts = sum(stats.count for stats in self.by_backend.values())
        if self.total_runs != sum_counts:
            raise ValueError(
                f"BackendDistributionResult.total_runs ({self.total_runs}) != "
                f"sum of counts ({sum_counts})"
            )
        if self.adoption_rate is not None and not (0 <= self.adoption_rate <= 100):
            raise ValueError(
                f"BackendDistributionResult.adoption_rate must be 0-100, got {self.adoption_rate}"
            )


@dataclass(frozen=True, slots=True)
class CacheEffectivenessStats:
    """Cache effectiveness statistics for a single backend.

    Invariants:
        - total_operations: Must equal hits + misses
        - hit_rate: Must equal hits / total_operations (0-1)
    """

    hits: int
    misses: int
    total_operations: int
    hit_rate: float

    def __post_init__(self) -> None:
        """Validate cache effectiveness invariants."""
        if self.hits < 0:
            raise ValueError(f"CacheEffectivenessStats.hits must be >= 0, got {self.hits}")
        if self.misses < 0:
            raise ValueError(
                f"CacheEffectivenessStats.misses must be >= 0, got {self.misses}"
            )
        if self.total_operations < 0:
            raise ValueError(
                f"CacheEffectivenessStats.total_operations must be >= 0, got {self.total_operations}"
            )
        # Verify total_operations equals hits + misses
        if self.total_operations != self.hits + self.misses:
            raise ValueError(
                f"CacheEffectivenessStats.total_operations ({self.total_operations}) != "
                f"hits ({self.hits}) + misses ({self.misses})"
            )
        # Verify hit_rate matches calculated value
        calculated_rate = self.hits / self.total_operations if self.total_operations > 0 else 0
        # Use epsilon based on rounding precision (round(x, 3) has max error 0.0005)
        if abs(self.hit_rate - calculated_rate) > 0.0005:
            raise ValueError(
                f"CacheEffectivenessStats.hit_rate ({self.hit_rate}) != "
                f"calculated ({calculated_rate})"
            )
        if not (0 <= self.hit_rate <= 1):
            raise ValueError(
                f"CacheEffectivenessStats.hit_rate must be 0-1, got {self.hit_rate}"
            )


@dataclass(frozen=True, slots=True)
class LockWaitStats:
    """Lock wait time statistics.

    Invariants:
        - p50_wait_ms: Must be <= p95_wait_ms
        - p95_wait_ms: Must be <= max_wait_ms
        - total_waits: Must be >= 0
    """

    total_waits: int
    avg_wait_ms: float
    p50_wait_ms: int
    p95_wait_ms: int
    max_wait_ms: int

    def __post_init__(self) -> None:
        """Validate lock wait statistics invariants."""
        if self.total_waits < 0:
            raise ValueError(
                f"LockWaitStats.total_waits must be >= 0, got {self.total_waits}"
            )
        if self.avg_wait_ms < 0:
            raise ValueError(
                f"LockWaitStats.avg_wait_ms must be >= 0, got {self.avg_wait_ms}"
            )
        # Verify percentile ordering: p50 <= p95 <= max
        if self.p50_wait_ms > self.p95_wait_ms:
            raise ValueError(
                f"LockWaitStats.p50_wait_ms ({self.p50_wait_ms}) > "
                f"p95_wait_ms ({self.p95_wait_ms})"
            )
        if self.p95_wait_ms > self.max_wait_ms:
            raise ValueError(
                f"LockWaitStats.p95_wait_ms ({self.p95_wait_ms}) > "
                f"max_wait_ms ({self.max_wait_ms})"
            )


@dataclass(frozen=True, slots=True)
class TimeoutStats:
    """Lock timeout statistics.

    Invariants:
        - count: Must be >= 0
        - rate_percent: Must be 0-100
    """

    count: int
    rate_percent: float

    def __post_init__(self) -> None:
        """Validate timeout statistics invariants."""
        if self.count < 0:
            raise ValueError(f"TimeoutStats.count must be >= 0, got {self.count}")
        if not (0 <= self.rate_percent <= 100):
            raise ValueError(
                f"TimeoutStats.rate_percent must be 0-100, got {self.rate_percent}"
            )


@dataclass(frozen=True, slots=True)
class LockContentionResult:
    """Result of lock contention analysis.

    Combines wait time statistics with timeout statistics.
    """

    lock_waits: LockWaitStats
    timeouts: TimeoutStats


@dataclass(frozen=True, slots=True)
class DbFileInfo:
    """Information about a single cache database file.

    Invariants:
        - size_mb: Must equal size_bytes / BYTES_TO_MB (within rounding)
        - size_bytes: Must be >= 0
    """

    name: str
    size_mb: float
    size_bytes: int
    modified: str

    def __post_init__(self) -> None:
        """Validate database file information invariants."""
        if not self.name:
            raise ValueError("DbFileInfo.name cannot be empty")
        if self.size_bytes < 0:
            raise ValueError(f"DbFileInfo.size_bytes must be >= 0, got {self.size_bytes}")
        if self.size_mb < 0:
            raise ValueError(f"DbFileInfo.size_mb must be >= 0, got {self.size_mb}")
        # Verify size_mb matches size_bytes (allowing for rounding)
        calculated_mb = round(self.size_bytes / BYTES_TO_MB, 4)
        if abs(self.size_mb - calculated_mb) > 0.0001:
            raise ValueError(
                f"DbFileInfo.size_mb ({self.size_mb}) != "
                f"calculated from size_bytes ({calculated_mb})"
            )


@dataclass(frozen=True, slots=True)
class DbGrowthResult:
    """Result of database growth scan.

    Invariants:
        - file_count: Must equal len(files)
        - total_size_mb: Must equal sum of file sizes
    """

    db_exists: bool
    total_size_mb: float
    file_count: int
    files: list[DbFileInfo]

    def __post_init__(self) -> None:
        """Validate database growth result invariants."""
        if self.total_size_mb < 0:
            raise ValueError(
                f"DbGrowthResult.total_size_mb must be >= 0, got {self.total_size_mb}"
            )
        if self.file_count < 0:
            raise ValueError(f"DbGrowthResult.file_count must be >= 0, got {self.file_count}")
        if self.file_count != len(self.files):
            raise ValueError(
                f"DbGrowthResult.file_count ({self.file_count}) != "
                f"len(files) ({len(self.files)})"
            )


@dataclass(frozen=True, slots=True)
class AnalysisPeriod:
    """Analysis period metadata.

    Invariants:
        - days_analyzed: Must be >= 1
    """

    start: str
    end: str
    days_analyzed: int
    total_events: int
    segment_path: str

    def __post_init__(self) -> None:
        """Validate analysis period invariants."""
        if self.days_analyzed < 1:
            raise ValueError(
                f"AnalysisPeriod.days_analyzed must be >= 1, got {self.days_analyzed}"
            )
        if self.total_events < 0:
            raise ValueError(
                f"AnalysisPeriod.total_events must be >= 0, got {self.total_events}"
            )


@dataclass(frozen=True, slots=True)
class AdoptionMetrics:
    """Complete adoption metrics result.

    Aggregates all analysis sections into a single result.
    """

    backend_distribution: BackendDistributionResult
    cache_effectiveness: dict[str, CacheEffectivenessStats]
    lock_contention: LockContentionResult
    db_growth: DbGrowthResult
    analysis_period: AnalysisPeriod | None = None


# ============================================================================
# Utility Functions
# ============================================================================


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )


def _dataclass_to_dict(obj: Any) -> Any:
    """Convert nested dataclasses to dict for JSON serialization.

    Recursively converts dataclass instances to dictionaries, preserving
    nested structures.
    """
    if hasattr(obj, "__dataclass_fields__"):
        return {
            k: _dataclass_to_dict(v)
            for k, v in asdict(obj).items()
        }
    elif isinstance(obj, dict):
        return {k: _dataclass_to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_dataclass_to_dict(item) for item in obj]
    else:
        return obj


def load_telemetry_events(events_path: Path) -> list[dict[str, Any]]:
    """Load all events from events.jsonl, skipping malformed lines.

    Args:
        events_path: Path to events.jsonl file.

    Returns:
        List of raw event dictionaries (not yet validated as TelemetryEvent).
    """
    events: list[dict[str, Any]] = []
    with open(events_path) as f:
        for line in f:
            line = line.strip()
            if not line or line == "[]":
                continue
            try:
                event = json.loads(line)
                events.append(event)
            except json.JSONDecodeError:
                continue
    return events


def filter_events_by_days(events: list[dict[str, Any]], days: int) -> list[dict[str, Any]]:
    """Filter events to last N days based on timestamp.

    Args:
        events: List of event dictionaries.
        days: Number of days to look back.

    Returns:
        Filtered list of events within the time window.
    """
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    return [e for e in events if e.get("ts", "") >= cutoff]


# ============================================================================
# Analysis Functions
# ============================================================================


def analyze_backend_distribution(events: list[dict[str, Any]]) -> BackendDistributionResult:
    """Analyze distribution of cache backends used.

    Args:
        events: List of event dictionaries.

    Returns:
        BackendDistributionResult with backend counts and percentages.
    """
    distribution: defaultdict[str, int] = defaultdict(int)

    for event in events:
        # Backend is stored in result.backend field
        backend = event.get("result", {}).get("backend", "Unknown")
        distribution[backend] += 1

    total = sum(distribution.values())
    if total == 0:
        return BackendDistributionResult(
            total_runs=0,
            by_backend={},
            adoption_rate=0.0
        )

    # Calculate percentages and create BackendStats
    by_backend: dict[str, BackendStats] = {}
    for backend, count in distribution.items():
        percentage = round(count / total * 100, 1)
        by_backend[backend] = BackendStats(count=count, percentage=percentage)

    # Validate percentages sum to ~100% (allow for rounding error)
    sum_percentages = sum(stats.percentage for stats in by_backend.values())
    if not (99.9 <= sum_percentages <= 100.1):
        raise ValueError(
            f"Backend percentages sum to {sum_percentages}, expected ~100.0. "
            f"This may indicate a calculation error."
        )

    # Extract FileLockedAstCache adoption rate
    adoption_rate = by_backend.get("FileLockedAstCache", BackendStats(count=0, percentage=0)).percentage

    return BackendDistributionResult(
        total_runs=total,
        by_backend=by_backend,
        adoption_rate=adoption_rate
    )


def analyze_cache_effectiveness(events: list[dict[str, Any]]) -> dict[str, CacheEffectivenessStats]:
    """Analyze cache hit/miss effectiveness by backend.

    Args:
        events: List of event dictionaries.

    Returns:
        Dict mapping backend names to CacheEffectivenessStats.
    """
    # Track hits and misses per backend
    backend_stats: defaultdict[str, dict[str, int]] = defaultdict(lambda: {"hits": 0, "misses": 0})

    for event in events:
        cmd = event.get("cmd")
        backend = event.get("result", {}).get("backend", "Unknown")

        if cmd == "ast.cache.hit":
            backend_stats[backend]["hits"] += 1
        elif cmd == "ast.cache.miss":
            backend_stats[backend]["misses"] += 1

    # Calculate hit rates and create CacheEffectivenessStats
    effectiveness: dict[str, CacheEffectivenessStats] = {}
    for backend, stats in backend_stats.items():
        hits = stats["hits"]
        misses = stats["misses"]
        total = hits + misses
        hit_rate = round(hits / total, 3) if total > 0 else 0.0

        effectiveness[backend] = CacheEffectivenessStats(
            hits=hits,
            misses=misses,
            total_operations=total,
            hit_rate=hit_rate
        )

    return effectiveness


def analyze_lock_contention(events: list[dict[str, Any]]) -> LockContentionResult:
    """Analyze lock wait and timeout events.

    Args:
        events: List of event dictionaries.

    Returns:
        LockContentionResult with wait time statistics and timeout counts.
    """
    lock_waits = []
    timeout_count = 0

    for event in events:
        cmd = event.get("cmd")
        timing = event.get("timing_ms", 0)

        if cmd == "ast.cache.lock_wait":
            lock_waits.append(timing)
        elif cmd == "ast.cache.lock_timeout":
            timeout_count += 1

    # Calculate wait time statistics
    if lock_waits:
        sorted_waits = sorted(lock_waits)
        n = len(sorted_waits)
        wait_stats = LockWaitStats(
            total_waits=len(lock_waits),
            avg_wait_ms=round(sum(lock_waits) / len(lock_waits), 1),
            p50_wait_ms=sorted_waits[int(n * 0.5)],
            p95_wait_ms=sorted_waits[int(n * 0.95)] if n > 1 else sorted_waits[0],
            max_wait_ms=sorted_waits[-1],
        )
    else:
        wait_stats = LockWaitStats(
            total_waits=0,
            avg_wait_ms=0.0,
            p50_wait_ms=0,
            p95_wait_ms=0,
            max_wait_ms=0,
        )

    total_contention_events = len(lock_waits) + timeout_count
    timeout_rate = round(timeout_count / max(1, total_contention_events) * 100, 2)

    timeout_stats = TimeoutStats(count=timeout_count, rate_percent=timeout_rate)

    return LockContentionResult(lock_waits=wait_stats, timeouts=timeout_stats)


def scan_db_growth(segment_path: Path) -> DbGrowthResult:
    """Scan AST cache database files for size and count.

    Args:
        segment_path: Root path to the segment being analyzed.

    Returns:
        DbGrowthResult with total size, file count, and per-file details.
    """
    cache_dir = segment_path / CACHE_DIR_NAME / CACHE_SUBDIR_NAME

    if not cache_dir.exists():
        return DbGrowthResult(
            db_exists=False,
            total_size_mb=0.0,
            file_count=0,
            files=[]
        )

    db_files = list(cache_dir.glob(CACHE_DB_PATTERN))

    if not db_files:
        return DbGrowthResult(
            db_exists=True,
            total_size_mb=0.0,
            file_count=0,
            files=[]
        )

    total_size = 0
    files_info = []

    for db_file in db_files:
        try:
            stat_result = db_file.stat()
            file_size = stat_result.st_size
            total_size += file_size

            files_info.append(DbFileInfo(
                name=db_file.name,
                size_mb=round(file_size / BYTES_TO_MB, 4),
                size_bytes=file_size,
                modified=datetime.fromtimestamp(stat_result.st_mtime).isoformat()
            ))
        except FileNotFoundError:
            # File was deleted between glob() and stat() - skip with warning
            logging.warning(f"Cache file deleted during scan: {db_file.name}")
            continue
        except OSError as e:
            # Other OS errors (permission denied, etc.)
            logging.error(f"Error accessing cache file {db_file.name}: {e}")
            continue

    # Sort by modified time (newest first)
    files_info.sort(key=lambda x: x.modified, reverse=True)

    return DbGrowthResult(
        db_exists=True,
        total_size_mb=round(total_size / BYTES_TO_MB, 4),
        file_count=len(files_info),
        files=files_info
    )


def analyze_adoption_metrics(
    events: list[dict[str, Any]],
    segment_path: Path
) -> AdoptionMetrics:
    """Analyze adoption metrics from filtered events.

    Args:
        events: List of event dictionaries.
        segment_path: Root path to scan for cache databases.

    Returns:
        AdoptionMetrics with all four analysis sections.
    """
    return AdoptionMetrics(
        backend_distribution=analyze_backend_distribution(events),
        cache_effectiveness=analyze_cache_effectiveness(events),
        lock_contention=analyze_lock_contention(events),
        db_growth=scan_db_growth(segment_path),
        analysis_period=None
    )


# ============================================================================
# CLI Entry Point
# ============================================================================


def main() -> None:
    """CLI entry point for adoption metrics analysis."""
    parser = argparse.ArgumentParser(description="Analyze AST cache adoption from telemetry")
    parser.add_argument("--segment", default=".", help="Segment path (default: .)")
    parser.add_argument("--days", type=int, default=7, help="Days to analyze (default: 7)")
    parser.add_argument("--out", required=True, help="Output JSON path")
    parser.add_argument(
        "--telemetry-file",
        default="_ctx/telemetry/events.jsonl",
        help="Path to events.jsonl"
    )
    args = parser.parse_args()

    segment_path = Path(args.segment).resolve()
    telemetry_path = segment_path / args.telemetry_file

    if not telemetry_path.exists():
        logging.error(f"Telemetry file not found: {telemetry_path}")
        sys.exit(1)

    # Calculate analysis period
    end_time = datetime.now()
    start_time = end_time - timedelta(days=args.days)

    logging.info(f"Loading telemetry from {telemetry_path}...")
    all_events = load_telemetry_events(telemetry_path)

    logging.info(f"Filtering events from last {args.days} days...")
    events = filter_events_by_days(all_events, args.days)

    logging.info(f"Analyzing {len(events)} events...")
    metrics = analyze_adoption_metrics(events, segment_path)

    # Add analysis period metadata
    analysis_period = AnalysisPeriod(
        start=start_time.isoformat(),
        end=end_time.isoformat(),
        days_analyzed=args.days,
        total_events=len(events),
        segment_path=str(segment_path)
    )

    # Create new metrics with analysis period
    metrics_with_period = AdoptionMetrics(
        backend_distribution=metrics.backend_distribution,
        cache_effectiveness=metrics.cache_effectiveness,
        lock_contention=metrics.lock_contention,
        db_growth=metrics.db_growth,
        analysis_period=analysis_period
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert dataclasses to dict for JSON serialization
    metrics_dict = _dataclass_to_dict(metrics_with_period)

    with open(out_path, "w") as f:
        json.dump(metrics_dict, f, indent=2)

    logging.info(f"Metrics written to {out_path}")
    print(json.dumps(metrics_dict, indent=2))


if __name__ == "__main__":
    setup_logging()
    main()
