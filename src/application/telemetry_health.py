"""Telemetry Health Check.

Provides health check functionality for Trifecta telemetry system.
Exit codes:
  0 = OK (all checks pass)
  2 = WARN (soft metrics exceeded threshold)
  3 = FAIL (hard invariants broken)

Health by Source:
  - operational: excludes source=fixture (real usage)
  - overall: includes all sources (for visibility)
  - Exit codes are based on operational ratio
"""

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

    def _compute_zero_hit_by_source(self) -> dict:
        """Compute zero-hit ratios by source from events.

        Returns:
            Dict with breakdown by source:
            {
                'overall': {'searches': N, 'zero_hits': M, 'ratio': R},
                'operational': {'searches': N, 'zero_hits': M, 'ratio': R},
                'sources': [{'source': 'fixture', 'searches': N, 'zero_hits': M, 'ratio': R}, ...]
            }
        """
        from collections import defaultdict

        # Count searches and zero-hits by source
        source_stats = defaultdict(lambda: {"searches": 0, "zero_hits": 0})

        for event in self.events:
            if event.get("cmd") != "ctx.search":
                continue

            source = event.get("x", {}).get("source", "unknown")
            hits = event.get("result", {}).get("hits", -1)

            source_stats[source]["searches"] += 1
            if hits == 0:
                source_stats[source]["zero_hits"] += 1

        # Compute ratios
        result = {
            "overall": {"searches": 0, "zero_hits": 0, "ratio": 0.0},
            "operational": {"searches": 0, "zero_hits": 0, "ratio": 0.0},
            "sources": [],
        }

        total_searches = 0
        total_zero_hits = 0
        operational_searches = 0
        operational_zero_hits = 0

        for source, stats in source_stats.items():
            searches = stats["searches"]
            zero_hits = stats["zero_hits"]
            ratio = zero_hits / searches if searches > 0 else 0.0

            result["sources"].append(
                {"source": source, "searches": searches, "zero_hits": zero_hits, "ratio": ratio}
            )

            total_searches += searches
            total_zero_hits += zero_hits

            # Operational excludes fixture
            if source != "fixture":
                operational_searches += searches
                operational_zero_hits += zero_hits

        # Overall ratio
        result["overall"]["searches"] = total_searches
        result["overall"]["zero_hits"] = total_zero_hits
        result["overall"]["ratio"] = total_zero_hits / total_searches if total_searches > 0 else 0.0

        # Operational ratio (excludes fixture)
        result["operational"]["searches"] = operational_searches
        result["operational"]["zero_hits"] = operational_zero_hits
        result["operational"]["ratio"] = (
            operational_zero_hits / operational_searches if operational_searches > 0 else 0.0
        )

        # Sort sources by zero-hits descending
        result["sources"].sort(key=lambda x: x["zero_hits"], reverse=True)

        return result

    def _compute_spanish_alias_impact(self) -> dict:
        from collections import defaultdict

        alias_events = [e for e in self.events if e.get("cmd") == "ctx.search.spanish_alias"]

        if not alias_events:
            return {
                "total_applied": 0,
                "total_recovered": 0,
                "recovery_rate": 0.0,
                "top_aliases": [],
            }

        total_applied = len(alias_events)

        total_recovered = 0
        alias_term_counts = defaultdict(int)
        known_spanish_terms = {
            "servicio",
            "servicios",
            "busqueda",
            "búsqueda",
            "documento",
            "configuracion",
            "configuración",
            "comando",
            "problema",
            "archivo",
            "carpeta",
            "directorio",
            "ruta",
            "código",
            "codigo",
            "proyecto",
            "aplicacion",
            "aplicación",
            "interfaz",
            "usuario",
            "datos",
            "informacion",
            "información",
            "resultado",
            "ejemplo",
            "prueba",
            "pruebas",
            "descripcion",
            "descripción",
        }

        for event in alias_events:
            query_preview = event.get("args", {}).get("query_preview", "") or event.get(
                "x", {}
            ).get("query_preview", "")
            recovered = event.get("result", {}).get("recovered", False)
            if recovered:
                total_recovered += 1
            if query_preview:
                lower_q = query_preview.lower()
                for term in known_spanish_terms:
                    if term in lower_q:
                        alias_term_counts[term] += 1

        top_aliases = [
            {"term": t, "count": c}
            for t, c in sorted(alias_term_counts.items(), key=lambda x: -x[1])
        ][:10]
        recovery_rate = total_recovered / total_applied if total_applied > 0 else 0.0

        return {
            "total_applied": total_applied,
            "total_recovered": total_recovered,
            "recovery_rate": recovery_rate,
            "top_aliases": top_aliases,
            "window_events": len(self.events),
        }

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
        """Check zero-hit ratio (soft metric).

        Uses operational ratio (excludes fixture) for exit code decisions.
        Reports both operational and overall for visibility.
        Prefers events.jsonl for accurate data, falls back to metrics.json.
        """
        source_breakdown = self._compute_zero_hit_by_source()

        operational = source_breakdown["operational"]
        overall = source_breakdown["overall"]

        ratio = operational["ratio"]
        total_searches = operational["searches"]
        zero_hits = operational["zero_hits"]

        if total_searches == 0:
            ratio = overall["ratio"]
            total_searches = overall["searches"]
            zero_hits = overall["zero_hits"]

        if total_searches == 0:
            metrics_searches = self.metrics.get("ctx_search_count", 0)
            metrics_zero_hits = self.metrics.get("ctx_search_zero_hits_count", 0)
            if metrics_searches > 0:
                ratio = metrics_zero_hits / metrics_searches
                total_searches = metrics_searches
                zero_hits = metrics_zero_hits

        if total_searches == 0:
            return None

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
            "operational_ratio": operational["ratio"],
            "operational_searches": operational["searches"],
            "operational_zero_hits": operational["zero_hits"],
            "overall_ratio": overall["ratio"],
            "overall_searches": overall["searches"],
            "overall_zero_hits": overall["zero_hits"],
            "source_breakdown": source_breakdown["sources"][:5],  # Top 5 sources
        }

        if top_zero_hits:
            details["top_zero_hit_queries"] = [
                {"query": h.get("query_preview", ""), "count": h.get("count", 0)}
                for h in top_zero_hits
            ]

        spanish_alias_impact = self._compute_spanish_alias_impact()
        if spanish_alias_impact["total_applied"] > 0:
            details["spanish_alias_impact"] = spanish_alias_impact

        if ratio > self.ZERO_HIT_RATIO_THRESHOLD:
            return HealthResult(
                status="WARN",
                message=f"Zero-hit ratio (operational) {ratio:.1%} exceeds threshold {self.ZERO_HIT_RATIO_THRESHOLD:.0%}",
                details=details,
            )

        return HealthResult(
            status="OK",
            message=f"Zero-hit ratio (operational) {ratio:.1%} within threshold",
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
            if "source_breakdown" in r.details:
                print("  Zero-hit by source:")
                for src in r.details["source_breakdown"]:
                    print(
                        f"    - {src['source']}: {src['zero_hits']}/{src['searches']} = {src['ratio']:.1%}"
                    )
            if "operational_ratio" in r.details:
                print(
                    f"  Operational (excl. fixture): {r.details['operational_zero_hits']}/{r.details['operational_searches']} = {r.details['operational_ratio']:.1%}"
                )
                print(
                    f"  Overall (all sources): {r.details['overall_zero_hits']}/{r.details['overall_searches']} = {r.details['overall_ratio']:.1%}"
                )
            if "spanish_alias_impact" in r.details:
                impact = r.details["spanish_alias_impact"]
                window = impact.get("window_events", "N/A")
                print(
                    f"  Spanish alias impact ({window} events): {impact['total_recovered']}/{impact['total_applied']} recovered ({impact['recovery_rate']:.1%} rate)"
                )
                if impact["top_aliases"]:
                    print("    Top aliases:")
                    for a in impact["top_aliases"][:5]:
                        print(f"      - {a['term']}: {a['count']}")

    if not results:
        print("No telemetry data found (WARN: no data to analyze)")
        return 2

    return exit_code
