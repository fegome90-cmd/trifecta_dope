# WO-0013: AST Persist Adoption Observability Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement telemetry analysis to monitor real-world adoption of AST cache persistence, tracking backend distribution, lock contention, and DB growth.

**Architecture:** Python script that parses `_ctx/telemetry/events.jsonl`, extracts metrics using the existing telemetry schema, and generates JSON metrics + markdown report. Uses patterns from `extract_ast_soak_metrics.py`.

**Tech Stack:** Python 3.11+, argparse, pathlib, json, pytest

**Context from Exploration:**
- Events schema: `cmd` field contains `ast.cache.hit/miss/write/lock_wait/lock_timeout`
- Backend field: `result.backend` = `"FileLockedAstCache"` | `"InMemoryLRUCache"`
- DB location: `.trifecta/cache/ast_cache_*.db`
- Reference script: `eval/scripts/extract_ast_soak_metrics.py`

**Worktree Location:** `.worktrees/wo0013-ast-adoption-observability`

---

## Task 1: Create Analysis Script Structure

**Files:**
- Create: `eval/scripts/analyze_adoption_telemetry.py`

**Step 1: Create script skeleton with imports and setup**

```python
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
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )


def load_telemetry_events(events_path: Path) -> list[dict[str, Any]]:
    """Load all events from events.jsonl, skipping malformed lines."""
    events = []
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


def filter_events_by_days(events: list[dict], days: int) -> list[dict]:
    """Filter events to last N days based on timestamp."""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    return [e for e in events if e.get("ts", "") >= cutoff]


def main():
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

    logging.info(f"Loading telemetry from {telemetry_path}...")
    all_events = load_telemetry_events(telemetry_path)

    logging.info(f"Filtering events from last {args.days} days...")
    events = filter_events_by_days(all_events, args.days)

    logging.info(f"Analyzing {len(events)} events...")
    metrics = analyze_adoption_metrics(events, segment_path)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w") as f:
        json.dump(metrics, f, indent=2)

    logging.info(f"Metrics written to {out_path}")
    print(json.dumps(metrics, indent=2))


def analyze_adoption_metrics(events: list[dict], segment_path: Path) -> dict[str, Any]:
    """Analyze adoption metrics from filtered events."""
    # Placeholder - implement in next task
    return {"placeholder": True}


if __name__ == "__main__":
    setup_logging()
    main()
```

**Step 2: Make script executable**

Run: `chmod +x eval/scripts/analyze_adoption_telemetry.py`
Expected: No output, file is now executable

**Step 3: Test basic execution (should fail gracefully)**

Run: `python eval/scripts/analyze_adoption_telemetry.py --out /tmp/test.json 2>&1 | head -5`
Expected: Error about telemetry file not found (expected in fresh run)

### 🔳 CHECKPOINT 1: Session Resume

**State after Task 1:**
- Script skeleton created at `eval/scripts/analyze_adoption_telemetry.py`
- File is executable
- Basic functions: `setup_logging()`, `load_telemetry_events()`, `filter_events_by_days()`
- Placeholder `analyze_adoption_metrics()` returns `{"placeholder": True}`

**To resume in new session:**
```bash
# Navigate to worktree
cd .worktrees/wo0013-ast-adoption-observability

# Verify script exists and is executable
ls -la eval/scripts/analyze_adoption_telemetry.py

# Continue with Task 2
```

**Next task:** Task 2 - Implement Backend Distribution Analysis

---

## Task 2: Implement Backend Distribution Analysis

**Files:**
- Modify: `eval/scripts/analyze_adoption_telemetry.py`

**Step 1: Add backend distribution function**

Add after `filter_events_by_days`:

```python
def analyze_backend_distribution(events: list[dict]) -> dict[str, Any]:
    """Analyze distribution of cache backends used.

    Returns:
        Dict with backend counts and percentages.
    """
    distribution = defaultdict(int)

    for event in events:
        # Backend is stored in result.backend field
        backend = event.get("result", {}).get("backend", "Unknown")
        distribution[backend] += 1

    total = sum(distribution.values())
    if total == 0:
        return {"total_runs": 0, "by_backend": {}}

    # Calculate percentages
    by_backend = {
        backend: {
            "count": count,
            "percentage": round(count / total * 100, 1)
        }
        for backend, count in distribution.items()
    }

    return {
        "total_runs": total,
        "by_backend": by_backend,
        "adoption_rate": by_backend.get("FileLockedAstCache", {}).get("percentage", 0)
    }
```

**Step 2: Update analyze_adoption_metrics to use new function**

Replace the placeholder:

```python
def analyze_adoption_metrics(events: list[dict], segment_path: Path) -> dict[str, Any]:
    """Analyze adoption metrics from filtered events."""
    return {
        "backend_distribution": analyze_backend_distribution(events),
    }
```

**Step 3: Test with real telemetry**

Run: `python eval/scripts/analyze_adoption_telemetry.py --segment . --days 7 --out /tmp/test_metrics.json`
Expected: JSON output with backend_distribution field

**Step 4: Verify output structure**

Run: `cat /tmp/test_metrics.json | jq '.backend_distribution'`
Expected: Shows total_runs and by_backend with FileLockedAstCache/InMemoryLRUCache

### 🔳 CHECKPOINT 2: Session Resume

**State after Task 2:**
- `analyze_backend_distribution()` function added
- Tracks backend usage: FileLockedAstCache vs InMemoryLRUCache
- Calculates adoption_rate percentage for FileLockedAstCache
- `analyze_adoption_metrics()` now returns backend_distribution

**To resume in new session:**
```bash
cd .worktrees/wo0013-ast-adoption-observability

# Verify backend distribution works
python eval/scripts/analyze_adoption_telemetry.py --segment . --days 7 --out /tmp/verify.json
cat /tmp/verify.json | jq '.backend_distribution'

# Continue with Task 3
```

**Next task:** Task 3 - Implement Cache Effectiveness Analysis

---

## Task 3: Implement Cache Effectiveness Analysis

**Files:**
- Modify: `eval/scripts/analyze_adoption_telemetry.py`

**Step 1: Add cache effectiveness function**

Add after `analyze_backend_distribution`:

```python
def analyze_cache_effectiveness(events: list[dict]) -> dict[str, Any]:
    """Analyze cache hit/miss effectiveness by backend.

    Returns:
        Dict with hit rates per backend type.
    """
    # Track hits and misses per backend
    backend_stats = defaultdict(lambda: {"hits": 0, "misses": 0})

    for event in events:
        cmd = event.get("cmd")
        backend = event.get("result", {}).get("backend", "Unknown")

        if cmd == "ast.cache.hit":
            backend_stats[backend]["hits"] += 1
        elif cmd == "ast.cache.miss":
            backend_stats[backend]["misses"] += 1

    # Calculate hit rates
    effectiveness = {}
    for backend, stats in backend_stats.items():
        total = stats["hits"] + stats["misses"]
        hit_rate = stats["hits"] / total if total > 0 else 0

        effectiveness[backend] = {
            "hits": stats["hits"],
            "misses": stats["misses"],
            "total_operations": total,
            "hit_rate": round(hit_rate, 3)
        }

    return effectiveness
```

**Step 2: Add to analyze_adoption_metrics return dict**

```python
def analyze_adoption_metrics(events: list[dict], segment_path: Path) -> dict[str, Any]:
    """Analyze adoption metrics from filtered events."""
    return {
        "backend_distribution": analyze_backend_distribution(events),
        "cache_effectiveness": analyze_cache_effectiveness(events),
    }
```

**Step 3: Test effectiveness calculation**

Run: `python eval/scripts/analyze_adoption_telemetry.py --segment . --days 7 --out /tmp/test_metrics.json`
Expected: cache_effectiveness field with hit rates per backend

**Step 4: Verify hit rate calculation**

Run: `cat /tmp/test_metrics.json | jq '.cache_effectiveness'`
Expected: Shows hits, misses, total_operations, hit_rate for each backend

### 🔳 CHECKPOINT 3: Session Resume

**State after Task 3:**
- `analyze_cache_effectiveness()` function added
- Tracks hit/miss rates per backend type
- Returns hit_rate as decimal (0.0 to 1.0)
- Metrics include: hits, misses, total_operations, hit_rate

**To resume in new session:**
```bash
cd .worktrees/wo0013-ast-adoption-observability

# Verify cache effectiveness works
python eval/scripts/analyze_adoption_telemetry.py --segment . --days 7 --out /tmp/verify.json
cat /tmp/verify.json | jq '.cache_effectiveness'

# Continue with Task 4
```

**Next task:** Task 4 - Implement Lock Contention Analysis

---

## Task 4: Implement Lock Contention Analysis

**Files:**
- Modify: `eval/scripts/analyze_adoption_telemetry.py`

**Step 1: Add lock contention function**

Add after `analyze_cache_effectiveness`:

```python
def analyze_lock_contention(events: list[dict]) -> dict[str, Any]:
    """Analyze lock wait and timeout events.

    Returns:
        Dict with contention statistics.
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
    wait_stats = {}
    if lock_waits:
        sorted_waits = sorted(lock_waits)
        n = len(sorted_waits)
        wait_stats = {
            "total_waits": len(lock_waits),
            "avg_wait_ms": round(sum(lock_waits) / len(lock_waits), 1),
            "p50_wait_ms": sorted_waits[int(n * 0.5)],
            "p95_wait_ms": sorted_waits[int(n * 0.95)],
            "max_wait_ms": sorted_waits[-1],
        }
    else:
        wait_stats = {
            "total_waits": 0,
            "avg_wait_ms": 0,
            "p50_wait_ms": 0,
            "p95_wait_ms": 0,
            "max_wait_ms": 0,
        }

    return {
        "lock_waits": wait_stats,
        "timeouts": {
            "count": timeout_count,
            "rate_percent": round(timeout_count / max(1, len(lock_waits) + timeout_count) * 100, 2)
        }
    }
```

**Step 2: Add to analyze_adoption_metrics**

```python
def analyze_adoption_metrics(events: list[dict], segment_path: Path) -> dict[str, Any]:
    """Analyze adoption metrics from filtered events."""
    return {
        "backend_distribution": analyze_backend_distribution(events),
        "cache_effectiveness": analyze_cache_effectiveness(events),
        "lock_contention": analyze_lock_contention(events),
    }
```

**Step 3: Test contention analysis**

Run: `python eval/scripts/analyze_adoption_telemetry.py --segment . --days 7 --out /tmp/test_metrics.json`
Expected: lock_contention field with wait stats and timeout count

**Step 4: Verify contention metrics**

Run: `cat /tmp/test_metrics.json | jq '.lock_contention'`
Expected: Shows total_waits, avg_wait_ms, timeouts count

### 🔳 CHECKPOINT 4: Session Resume

**State after Task 4:**
- `analyze_lock_contention()` function added
- Tracks lock wait times (avg, p50, p95, max)
- Counts timeout events and calculates timeout rate
- Returns lock_waits and timeouts sections

**To resume in new session:**
```bash
cd .worktrees/wo0013-ast-adoption-observability

# Verify lock contention works
python eval/scripts/analyze_adoption_telemetry.py --segment . --days 7 --out /tmp/verify.json
cat /tmp/verify.json | jq '.lock_contention'

# Continue with Task 5
```

**Next task:** Task 5 - Implement DB Growth Analysis

---

## Task 5: Implement DB Growth Analysis

**Files:**
- Modify: `eval/scripts/analyze_adoption_telemetry.py`

**Step 1: Add DB scan function**

Add after `analyze_lock_contention`:

```python
def scan_db_growth(segment_path: Path) -> dict[str, Any]:
    """Scan AST cache database files for size and count.

    Returns:
        Dict with total size, file count, and per-file details.
    """
    cache_dir = segment_path / ".trifecta" / "cache"

    if not cache_dir.exists():
        return {
            "db_exists": False,
            "total_size_mb": 0,
            "file_count": 0,
            "files": []
        }

    db_files = list(cache_dir.glob("ast_cache_*.db"))

    if not db_files:
        return {
            "db_exists": True,
            "total_size_mb": 0,
            "file_count": 0,
            "files": []
        }

    total_size = sum(f.stat().st_size for f in db_files)
    files = [
        {
            "name": f.name,
            "size_mb": round(f.stat().st_size / (1024 * 1024), 4),
            "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
        }
        for f in db_files
    ]

    return {
        "db_exists": True,
        "total_size_mb": round(total_size / (1024 * 1024), 4),
        "file_count": len(db_files),
        "files": files
    }
```

**Step 2: Add to analyze_adoption_metrics**

```python
def analyze_adoption_metrics(events: list[dict], segment_path: Path) -> dict[str, Any]:
    """Analyze adoption metrics from filtered events."""
    return {
        "backend_distribution": analyze_backend_distribution(events),
        "cache_effectiveness": analyze_cache_effectiveness(events),
        "lock_contention": analyze_lock_contention(events),
        "db_growth": scan_db_growth(segment_path),
    }
```

**Step 3: Test DB scanning**

Run: `python eval/scripts/analyze_adoption_telemetry.py --segment . --days 7 --out /tmp/test_metrics.json`
Expected: db_growth field with size and file count

**Step 4: Verify DB metrics**

Run: `cat /tmp/test_metrics.json | jq '.db_growth'`
Expected: Shows total_size_mb, file_count, and file details

### 🔳 CHECKPOINT 5: Session Resume

**State after Task 5:**
- `scan_db_growth()` function added
- Scans `.trifecta/cache/ast_cache_*.db` files
- Returns: db_exists, total_size_mb, file_count, files[]
- Each file entry: name, size_mb, modified timestamp

**To resume in new session:**
```bash
cd .worktrees/wo0013-ast-adoption-observability

# Verify DB growth scan works
python eval/scripts/analyze_adoption_telemetry.py --segment . --days 7 --out /tmp/verify.json
cat /tmp/verify.json | jq '.db_growth'

# Continue with Task 6
```

**Next task:** Task 6 - Add Analysis Period Metadata

---

## Task 6: Add Analysis Period Metadata

**Files:**
- Modify: `eval/scripts/analyze_adoption_telemetry.py`

**Step 1: Add period calculation to main**

Update the main function to add period metadata:

```python
def main():
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

    # Add metadata
    metrics["analysis_period"] = {
        "start": start_time.isoformat(),
        "end": end_time.isoformat(),
        "days_analyzed": args.days,
        "total_events": len(events),
        "segment_path": str(segment_path)
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w") as f:
        json.dump(metrics, f, indent=2)

    logging.info(f"Metrics written to {out_path}")
    print(json.dumps(metrics, indent=2))
```

**Step 2: Test metadata inclusion**

Run: `python eval/scripts/analyze_adoption_telemetry.py --segment . --days 7 --out /tmp/test_metrics.json`
Expected: analysis_period field with start/end times

**Step 3: Verify period calculation**

Run: `cat /tmp/test_metrics.json | jq '.analysis_period'`
Expected: Shows start, end, days_analyzed, total_events

### 🔳 CHECKPOINT 6: Session Resume

**State after Task 6:**
- Analysis period metadata added to output
- Tracks: start, end, days_analyzed, total_events, segment_path
- Full script implementation complete (all analysis functions working)

**To resume in new session:**
```bash
cd .worktrees/wo0013-ast-adoption-observability

# Verify complete script works
python eval/scripts/analyze_adoption_telemetry.py --segment . --days 7 --out /tmp/verify.json
cat /tmp/verify.json | jq .

# Continue with Task 7
```

**Next task:** Task 7 - Generate Initial Metrics and Report

---

## Task 7: Generate Initial Metrics and Report

**Files:**
- Create: `_ctx/metrics/wo0013_adoption_baseline.json`
- Create: `docs/reports/wo0013_adoption_observability.md`

**Step 1: Run analysis to generate baseline metrics**

Run: `python eval/scripts/analyze_adoption_telemetry.py --segment . --days 7 --out _ctx/metrics/wo0013_adoption_baseline.json`
Expected: JSON metrics written to _ctx/metrics/

**Step 2: Create audit report template**

Create `docs/reports/wo0013_adoption_observability.md`:

```markdown
# WO-0013: AST Persist Adoption Observability Report

## Evidence Header
- **WO**: WO-0013
- **SHA**: `<commit SHA after completion>`
- **Analysis Date**: `{date}`
- **Data Source**: `_ctx/telemetry/events.jsonl`
- **Analysis Period**: `{start} to {end}`
- **Method**: Telemetry event analysis via `analyze_adoption_telemetry.py`

---

## Executive Summary

<!-- Fill after running analysis -->

## Backend Distribution

| Backend | Runs | Percentage |
|---------|------|------------|
<!-- Fill from metrics -->

## Cache Effectiveness

| Backend | Hit Rate | Hits | Misses |
|---------|----------|------|--------|
<!-- Fill from metrics -->

## Lock Contention

| Metric | Value |
|--------|-------|
| Total Lock Waits | `{value}` |
| Avg Wait Time | `{value} ms` |
| Timeouts | `{value}` |
| Timeout Rate | `{value}%` |

## Database Growth

| Metric | Value |
|--------|-------|
| DB Exists | `{yes/no}` |
| Total Size | `{value} MB` |
| File Count | `{value}` |

## Anomalies Detected

<!-- List any issues found -->

## Recommendations

<!-- Actionable insights based on findings -->

---

## Appendix: Full Metrics

See `_ctx/metrics/wo0013_adoption_baseline.json` for complete data.
```

**Step 3: Fill report with actual metrics**

Run: `cat _ctx/metrics/wo0013_adoption_baseline.json | jq .`
Expected: Review metrics and manually update the markdown report

### 🔳 CHECKPOINT 7: Session Resume

**State after Task 7:**
- Baseline metrics generated at `_ctx/metrics/wo0013_adoption_baseline.json`
- Report template created at `docs/reports/wo0013_adoption_observability.md`
- Report needs to be filled with actual metrics from baseline JSON

**To resume in new session:**
```bash
cd .worktrees/wo0013-ast-adoption-observability

# Verify baseline exists
cat _ctx/metrics/wo0013_adoption_baseline.json | jq .

# Continue with Task 8
```

**Next task:** Task 8 - Write Unit Tests

---

## Task 8: Write Unit Tests

**Files:**
- Create: `tests/unit/test_analyze_adoption_telemetry.py`

**Step 1: Create test file with basic structure**

```python
import json
import pytest
from pathlib import Path
from eval.scripts.analyze_adoption_telemetry import (
    analyze_backend_distribution,
    analyze_cache_effectiveness,
    analyze_lock_contention,
    filter_events_by_days,
)


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
    ]


def test_backend_distribution_counts_correctly(sample_events):
    """Test that backend distribution is calculated correctly."""
    result = analyze_backend_distribution(sample_events)

    assert result["total_runs"] == 2
    assert result["by_backend"]["FileLockedAstCache"]["count"] == 1
    assert result["by_backend"]["InMemoryLRUCache"]["count"] == 1
    assert result["adoption_rate"] == 50.0


def test_cache_effectiveness_calculates_hit_rate(sample_events):
    """Test that cache hit rate is calculated correctly."""
    result = analyze_cache_effectiveness(sample_events)

    assert "FileLockedAstCache" in result
    assert result["FileLockedAstCache"]["hits"] == 1
    assert result["FileLockedAstCache"]["misses"] == 1
    assert result["FileLockedAstCache"]["hit_rate"] == 0.5


def test_lock_contention_handles_no_events():
    """Test that lock contention handles empty event list."""
    result = analyze_lock_contention([])

    assert result["lock_waits"]["total_waits"] == 0
    assert result["timeouts"]["count"] == 0


def test_filter_events_by_days_filters_correctly():
    """Test time-based filtering."""
    events = [
        {"ts": "2026-01-01T12:00:00Z"},
        {"ts": "2026-01-09T12:00:00Z"},
    ]

    # Filter for last 1 day (should only keep recent event)
    result = filter_events_by_days(events, days=1)

    assert len(result) == 1
    assert result[0]["ts"] == "2026-01-09T12:00:00Z"
```

**Step 2: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_analyze_adoption_telemetry.py -v`
Expected: All tests PASS

### 🔳 CHECKPOINT 8: Session Resume

**State after Task 8:**
- Unit test file created at `tests/unit/test_analyze_adoption_telemetry.py`
- 4 test cases covering: backend distribution, cache effectiveness, lock contention, time filtering
- All tests passing

**To resume in new session:**
```bash
cd .worktrees/wo0013-ast-adoption-observability

# Verify tests pass
uv run pytest tests/unit/test_analyze_adoption_telemetry.py -v

# Continue with Task 9
```

**Next task:** Task 9 - Update Session Documentation

---

## Task 9: Update Session Documentation

**Files:**
- Modify: `_ctx/session_trifecta_dope.md`

**Step 1: Append session entry**

Add to end of `_ctx/session_trifecta_dope.md`:

```markdown
## YYYY-MM-DD HH:MM UTC - WO-0013 COMPLETE
- **Summary**: AST Persist Adoption Observability implemented
- **Files Created**:
  - `eval/scripts/analyze_adoption_telemetry.py` - Main analysis script
  - `docs/reports/wo0013_adoption_observability.md` - Audit report
  - `tests/unit/test_analyze_adoption_telemetry.py` - Unit tests
- **Commands**:
  - `python eval/scripts/analyze_adoption_telemetry.py --segment . --days 7 --out _ctx/metrics/wo0013_adoption_baseline.json`
- **Evidence**: _ctx/metrics/wo0013_adoption_baseline.json
- **Metrics**:
  - Backend adoption: {X}% FileLockedAstCache
  - Cache effectiveness: {X}% hit rate
  - Lock contention: {X} timeout events
  - DB size: {X} MB
- **Tests**: 4/4 unit tests PASS
- **Next**: Monitor adoption trends over time, re-run analysis weekly
```

**Step 2: Verify session update**

Run: `tail -20 _ctx/session_trifecta_dope.md`
Expected: New session entry visible

### 🔳 CHECKPOINT 9: Session Resume

**State after Task 9:**
- Session documentation updated in `_ctx/session_trifecta_dope.md`
- WO-0013 completion entry added with summary, files, commands, metrics

**To resume in new session:**
```bash
cd .worktrees/wo0013-ast-adoption-observability

# Verify session entry
tail -20 _ctx/session_trifecta_dope.md

# Continue with Task 10
```

**Next task:** Task 10 - Final Verification and Commit

---

## Task 10: Final Verification and Commit

**Files:**
- Git add and commit all changes

**Step 1: Run all tests**

Run: `uv run pytest -q tests/unit/test_analyze_adoption_telemetry.py tests/integration/test_ast_cache_telemetry.py`
Expected: All tests PASS

**Step 2: Verify script execution**

Run: `python eval/scripts/analyze_adoption_telemetry.py --segment . --days 7 --out _ctx/metrics/wo0013_verify.json && cat _ctx/metrics/wo0013_verify.json | jq .analysis_period`
Expected: Valid JSON with analysis_period field

**Step 3: Move WO to done**

Run: `mv _ctx/jobs/pending/WO-0013.yaml _ctx/jobs/done/WO-0013.yaml`
Expected: File moved to done/

**Step 4: Update WO with completion SHA**

Edit `_ctx/jobs/done/WO-0013.yaml`:
- Set `verified_at_sha` to actual commit SHA
- Set `closed_at` to current timestamp

**Step 5: Commit all changes**

```bash
git add eval/scripts/analyze_adoption_telemetry.py
git add docs/reports/wo0013_adoption_observability.md
git add tests/unit/test_analyze_adoption_telemetry.py
git add _ctx/jobs/done/WO-0013.yaml
git add _ctx/session_trifecta_dope.md
git add _ctx/metrics/wo0013_adoption_baseline.json

git commit -m "feat(wo0013): add AST adoption observability

- Added analyze_adoption_telemetry.py script
- Tracks backend distribution, cache effectiveness, lock contention
- Added unit tests for analysis functions
- Generated baseline adoption report
- WO-0013 COMPLETE"
```

**Step 6: Verify commit**

Run: `git log -1 --stat`
Expected: Shows all modified/created files

### ✅ FINAL CHECKPOINT: WO-0013 COMPLETE

**State after Task 10:**
- All tests passing
- Script verified working
- WO moved to done/ with SHA
- Git commit created with all files
- Worktree ready for cleanup

**To continue after merge:**
```bash
# After PR merge, cleanup worktree
git worktree remove .worktrees/wo0013-ast-adoption-observability

# Delete local branch
git branch -d wo0013-ast-adoption-observability
```

---

## Verification Checklist

After implementation, verify:

- [ ] Script runs without errors: `python eval/scripts/analyze_adoption_telemetry.py --segment . --days 7 --out /tmp/test.json`
- [ ] Output is valid JSON: `cat /tmp/test.json | jq .`
- [ ] All required fields present: backend_distribution, cache_effectiveness, lock_contention, db_growth
- [ ] Unit tests pass: `pytest tests/unit/test_analyze_adoption_telemetry.py -v`
- [ ] Integration tests pass: `pytest tests/integration/test_ast_cache_telemetry.py -v`
- [ ] Report generated: `ls -la docs/reports/wo0013_adoption_observability.md`
- [ ] Session updated: `grep "WO-0013" _ctx/session_trifecta_dope.md`
- [ ] WO moved to done: `ls _ctx/jobs/done/WO-0013.yaml`
- [ ] Git commit created with all files

---

## Usage Examples

After implementation:

```bash
# Analyze last 7 days
python eval/scripts/analyze_adoption_telemetry.py --segment . --days 7 --out _ctx/metrics/wo0013_adoption.json

# Analyze last 30 days
python eval/scripts/analyze_adoption_telemetry.py --segment . --days 30 --out _ctx/metrics/wo0013_adoption_30d.json

# View metrics
cat _ctx/metrics/wo0013_adoption.json | jq .

# Check adoption rate
cat _ctx/metrics/wo0013_adoption.json | jq '.backend_distribution.adoption_rate'
```
