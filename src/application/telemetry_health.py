"""Telemetry Health Check.

Provides health check functionality for Trifecta telemetry system.
Exit codes:
  0 = OK (all checks pass)
  2 = WARN (soft metrics exceeded threshold)
  3 = FAIL (hard invariants broken)
"""

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from src.application.telemetry_reports import load_telemetry_data
from src.application.zero_hit_tracker import create_zero_hit_tracker


@dataclass
class HealthResult:
    """Result of a health check."""

    status: str  # "OK", "WARN", "FAIL"
    message: str
    details: dict


class TelemetryHealth:
    """Health checker for telemetry data."""

    ZERO_HIT_RATIO_THRESHOLD = 0.30  # 30% warning threshold

    def __init__(self, segment_path: Path):
        self.segment_path = segment_path
        self.events: list = []
        self.metrics: dict = {}
        self.last_run: dict = {}
        self._load_data()

    def _load_data(self):
        """Load telemetry data from segment."""
        self.events, self.metrics, self.last_run = load_telemetry_data(self.segment_path)

    def check_lsp_invariants(self) -> list[HealthResult]:
        """Check hard LSP invariants."""
        results = []

        ready_fail = self.metrics.get("lsp.ready_fail_invariant", 0)
        if ready_fail > 0:
            results.append(
                HealthResult(
                    status="FAIL",
                    message=f"lsp.ready_fail_invariant = {ready_fail} (hard invariant broken)",
                    details={"metric": "lsp.ready_fail_invariant", "value": ready_fail},
                )
            )

        thread_alive = self.metrics.get("lsp.thread_alive_after_join", 0)
        if thread_alive > 0:
            results.append(
                HealthResult(
                    status="FAIL",
                    message=f"lsp.thread_alive_after_join = {thread_alive} (hard invariant broken)",
                    details={"metric": "lsp.thread_alive_after_join", "value": thread_alive},
                )
            )

        return results

    def check_zero_hit_ratio(self) -> Optional[HealthResult]:
        """Check zero-hit ratio (soft metric)."""
        total_searches = self.metrics.get("ctx_search_count", 0)
        if total_searches == 0:
            return None

        zero_hits = self.metrics.get("ctx_search_zero_hits_count", 0)
        ratio = zero_hits / total_searches if total_searches > 0 else 0

        # Get top zero-hit queries from tracker
        top_zero_hits = []
        try:
            tracker = create_zero_hit_tracker(self.segment_path / "_ctx" / "telemetry")
            top_zero_hits = tracker.get_top_zero_hits(limit=5)
        except Exception:
            pass  # Non-blocking

        details = {
            "metric": "zero_hit_ratio",
            "value": ratio,
            "threshold": self.ZERO_HIT_RATIO_THRESHOLD,
            "total_searches": total_searches,
            "zero_hits": zero_hits,
        }

        if top_zero_hits:
            details["top_zero_hit_queries"] = [
                {"query": h.get("query_preview", ""), "count": h.get("count", 0)}
                for h in top_zero_hits
            ]

        if ratio > self.ZERO_HIT_RATIO_THRESHOLD:
            return HealthResult(
                status="WARN",
                message=f"Zero-hit ratio {ratio:.1%} exceeds threshold {self.ZERO_HIT_RATIO_THRESHOLD:.0%}",
                details=details,
            )

        return HealthResult(
            status="OK",
            message=f"Zero-hit ratio {ratio:.1%} within threshold",
            details=details,
        )

    def check_all(self) -> tuple[int, list[HealthResult]]:
        """Run all health checks.

        Returns:
            Tuple of (exit_code, results)
        """
        results = []

        results.extend(self.check_lsp_invariants())

        zero_hit = self.check_zero_hit_ratio()
        if zero_hit:
            results.append(zero_hit)

        fail_count = sum(1 for r in results if r.status == "FAIL")
        warn_count = sum(1 for r in results if r.status == "WARN")

        if fail_count > 0:
            return 3, results
        elif warn_count > 0:
            return 2, results
        else:
            return 0, results


def run_health_check(segment_path: Path, verbose: bool = False) -> int:
    """Run health check and return exit code.

    Args:
        segment_path: Path to segment directory
        verbose: Print detailed information including top queries

    Returns:
        Exit code: 0=OK, 2=WARN, 3=FAIL
    """
    health = TelemetryHealth(segment_path)
    exit_code, results = health.check_all()

    for r in results:
        status_icon = {"OK": "✓", "WARN": "⚠", "FAIL": "✗"}[r.status]
        print(f"{status_icon} {r.message}")

        # Print detailed info for WARN/FAIL or when verbose
        if verbose or r.status in ("WARN", "FAIL"):
            if "top_zero_hit_queries" in r.details:
                print("  Top zero-hit queries:")
                for q in r.details["top_zero_hit_queries"][:5]:
                    print(f"    - {q['query']} (count: {q['count']})")
            if "total_searches" in r.details:
                print(
                    f"  Total searches: {r.details['total_searches']}, Zero-hits: {r.details['zero_hits']}"
                )

    if not results:
        print("No telemetry data found (WARN: no data to analyze)")
        return 2

    return exit_code
