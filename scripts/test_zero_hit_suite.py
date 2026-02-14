#!/usr/bin/env python3
"""Zero-Hit Testing Suite - Search and Collect Metrics.

Executes a comprehensive set of search queries and collects zero-hit metrics
to validate interventions and identify remaining zero-hit patterns.

Usage:
    python scripts/test_zero_hit_suite.py --segment . --output report.json
    python scripts/test_zero_hit_suite.py --segment . --format markdown
"""

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class SearchResult:
    """Result from a single search query."""

    query: str
    category: str  # empty, vague, short, spanish, english, technical
    hits: int
    zero_hit: bool
    rejected: bool
    rejection_reason: Optional[str] = None
    latency_ms: float = 0.0
    error: Optional[str] = None


@dataclass
class TestSuiteReport:
    """Complete report from test suite execution."""

    timestamp: str
    segment: str
    total_queries: int
    zero_hits: int
    rejected: int
    errors: int
    zero_hit_ratio: float
    by_category: Dict[str, Dict] = field(default_factory=dict)
    results: List[SearchResult] = field(default_factory=list)


class ZeroHitTestSuite:
    """Test suite for zero-hit analysis."""

    # Test query categories with expected behaviors
    TEST_QUERIES = {
        "empty": [
            "",
            "   ",
            "\t\n",
        ],
        "vague": [
            "a",
            "x",
            "ab",
            "test",
            "query",
        ],
        "short": [
            "ok",
            "no",
            "up",
        ],
        "spanish": [
            "servicio",
            "servicios",
            "documentación",
            "guía",
            "manual",
            "comandos",
            "error",
            "telemetría",
            "métricas",
            "búsqueda",
            "contexto",
            "consulta",
            "cómo usar",
            "guía de usuario",
        ],
        "english_common": [
            "service",
            "services",
            "documentation",
            "guide",
            "manual",
            "commands",
            "error",
            "telemetry",
            "metrics",
            "search",
            "context",
            "query",
            "how to use",
            "user guide",
        ],
        "technical": [
            "ctx.search",
            "ctx.get",
            "telemetry event",
            "zero hit",
            "stop_reason",
            "context pack",
            "trifecta",
        ],
        "edge_cases": [
            "123",
            "!!!",
            "@#$%",
            "mixed123",
            "UPPERCASE",
            "MixedCase",
        ],
    }

    def __init__(self, segment_path: Path, verbose: bool = False):
        self.segment_path = segment_path
        self.verbose = verbose
        self.results: List[SearchResult] = []

    def _run_search(self, query: str) -> tuple[int, bool, Optional[str]]:
        """Execute search query and return (hits, is_zero_hit, error)."""
        start_time = time.time()

        try:
            # Build command
            cmd = [
                sys.executable,
                "-m",
                "src.infrastructure.cli",
                "ctx",
                "search",
                "--segment",
                str(self.segment_path),
                "--query",
                query,
                "--limit",
                "5",
            ]

            # Execute search
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
            )

            latency_ms = (time.time() - start_time) * 1000

            # Parse output
            output = result.stdout + result.stderr

            # Check for rejection (B2 intervention)
            if "rejected" in output.lower() or "Query rejected" in output:
                return 0, True, None  # Zero hit because rejected

            # Check for hits
            if "No results found" in output or result.returncode != 0:
                return 0, True, None  # Zero hit

            # Count hits (look for "X hits" in output)
            hits = 0
            for line in output.split("\n"):
                if "hits" in line.lower():
                    try:
                        # Extract number before "hits"
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if "hits" in part.lower() and i > 0:
                                hits = int(parts[i - 1])
                                break
                    except (ValueError, IndexError):
                        pass

            return hits, hits == 0, None

        except subprocess.TimeoutExpired:
            return 0, True, "Timeout"
        except Exception as e:
            return 0, True, str(e)

    def run_suite(self) -> TestSuiteReport:
        """Execute complete test suite."""
        print(f"🧪 Running Zero-Hit Test Suite on {self.segment_path}")
        print("=" * 70)

        total_queries = 0
        zero_hits = 0
        rejected = 0
        errors = 0
        by_category = {}

        for category, queries in self.TEST_QUERIES.items():
            if self.verbose:
                print(f"\n📂 Category: {category}")

            category_zero_hits = 0
            category_rejected = 0
            category_total = 0

            for query in queries:
                total_queries += 1
                category_total += 1

                hits, is_zero_hit, error = self._run_search(query)

                # Check if rejected (B2)
                is_rejected = False
                rejection_reason = None
                if is_zero_hit and len(query) < 2:
                    is_rejected = True
                    rejection_reason = "Query too short (B2)"
                    rejected += 1
                    category_rejected += 1

                if is_zero_hit and not is_rejected:
                    zero_hits += 1
                    category_zero_hits += 1

                if error:
                    errors += 1

                result = SearchResult(
                    query=query,
                    category=category,
                    hits=hits,
                    zero_hit=is_zero_hit and not is_rejected,
                    rejected=is_rejected,
                    rejection_reason=rejection_reason,
                    error=error,
                )
                self.results.append(result)

                if self.verbose:
                    status = "✅" if not is_zero_hit else "❌"
                    if is_rejected:
                        status = "🚫"
                    print(f"  {status} '{query[:30]}...' -> {hits} hits")

            by_category[category] = {
                "total": category_total,
                "zero_hits": category_zero_hits,
                "rejected": category_rejected,
                "zero_hit_rate": (category_zero_hits / category_total * 100)
                if category_total > 0
                else 0,
            }

        # Calculate overall ratio
        # Note: Rejected queries are NOT counted as zero-hits (they're prevented)
        valid_queries = total_queries - rejected
        zero_hit_ratio = (zero_hits / valid_queries * 100) if valid_queries > 0 else 0

        report = TestSuiteReport(
            timestamp=datetime.now().isoformat(),
            segment=str(self.segment_path),
            total_queries=total_queries,
            zero_hits=zero_hits,
            rejected=rejected,
            errors=errors,
            zero_hit_ratio=zero_hit_ratio,
            by_category=by_category,
            results=self.results,
        )

        return report

    def print_summary(self, report: TestSuiteReport):
        """Print summary report to console."""
        print("\n" + "=" * 70)
        print("📊 ZERO-HIT TEST SUITE RESULTS")
        print("=" * 70)
        print(f"Timestamp: {report.timestamp}")
        print(f"Segment: {report.segment}")
        print()
        print(f"Total Queries:     {report.total_queries}")
        print(f"Rejected (B2):     {report.rejected}")
        print(f"Valid Queries:     {report.total_queries - report.rejected}")
        print(f"Zero Hits:         {report.zero_hits}")
        print(f"Errors:            {report.errors}")
        print()
        print(f"🎯 Zero-Hit Ratio: {report.zero_hit_ratio:.2f}%")
        print(f"   (excluding rejected queries)")
        print()

        print("📈 By Category:")
        print("-" * 70)
        for category, stats in report.by_category.items():
            print(
                f"  {category:15} | Total: {stats['total']:3} | "
                f"Zero: {stats['zero_hits']:3} | "
                f"Rejected: {stats['rejected']:3} | "
                f"Rate: {stats['zero_hit_rate']:5.1f}%"
            )

        print()

        # Show zero-hit queries for analysis
        if report.zero_hits > 0:
            print("❌ Zero-Hit Queries (for analysis):")
            print("-" * 70)
            for result in report.results:
                if result.zero_hit and not result.rejected:
                    print(f"  [{result.category:12}] '{result.query}'")

        print()

        # Show rejected queries (B2 working)
        if report.rejected > 0:
            print("🚫 Rejected Queries (B2 Intervention working):")
            print("-" * 70)
            for result in report.results:
                if result.rejected:
                    print(f"  [{result.category:12}] '{result.query}' -> {result.rejection_reason}")

        print()


def save_json_report(report: TestSuiteReport, output_path: Path):
    """Save report as JSON."""
    data = {
        "timestamp": report.timestamp,
        "segment": report.segment,
        "summary": {
            "total_queries": report.total_queries,
            "zero_hits": report.zero_hits,
            "rejected": report.rejected,
            "errors": report.errors,
            "zero_hit_ratio": report.zero_hit_ratio,
        },
        "by_category": report.by_category,
        "results": [
            {
                "query": r.query,
                "category": r.category,
                "hits": r.hits,
                "zero_hit": r.zero_hit,
                "rejected": r.rejected,
                "rejection_reason": r.rejection_reason,
                "error": r.error,
            }
            for r in report.results
        ],
    }

    output_path.write_text(json.dumps(data, indent=2))
    print(f"📄 JSON report saved to: {output_path}")


def save_markdown_report(report: TestSuiteReport, output_path: Path):
    """Save report as Markdown."""
    lines = [
        "# Zero-Hit Test Suite Report",
        "",
        f"**Generated**: {report.timestamp}",
        f"**Segment**: {report.segment}",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total Queries | {report.total_queries} |",
        f"| Rejected (B2) | {report.rejected} |",
        f"| Valid Queries | {report.total_queries - report.rejected} |",
        f"| Zero Hits | {report.zero_hits} |",
        f"| **Zero-Hit Ratio** | **{report.zero_hit_ratio:.2f}%** |",
        "",
        "## Results by Category",
        "",
        "| Category | Total | Zero Hits | Rejected | Rate |",
        "|----------|-------|-----------|----------|------|",
    ]

    for category, stats in report.by_category.items():
        lines.append(
            f"| {category} | {stats['total']} | {stats['zero_hits']} | "
            f"{stats['rejected']} | {stats['zero_hit_rate']:.1f}% |"
        )

    lines.extend(
        [
            "",
            "## Zero-Hit Queries",
            "",
        ]
    )

    zero_hit_results = [r for r in report.results if r.zero_hit and not r.rejected]
    if zero_hit_results:
        lines.append("| Category | Query |")
        lines.append("|----------|-------|")
        for r in zero_hit_results:
            lines.append(f"| {r.category} | `{r.query}` |")
    else:
        lines.append("No zero-hit queries found! 🎉")

    lines.extend(
        [
            "",
            "## Rejected Queries (B2)",
            "",
        ]
    )

    rejected_results = [r for r in report.results if r.rejected]
    if rejected_results:
        lines.append("| Category | Query | Reason |")
        lines.append("|----------|-------|--------|")
        for r in rejected_results:
            lines.append(f"| {r.category} | `{r.query}` | {r.rejection_reason} |")
    else:
        lines.append("No queries were rejected.")

    output_path.write_text("\n".join(lines))
    print(f"📄 Markdown report saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Zero-Hit Testing Suite - Search and Collect Metrics"
    )
    parser.add_argument(
        "--segment",
        type=Path,
        default=Path("."),
        help="Path to segment (default: current directory)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output file path for JSON report",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["json", "markdown", "md"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    # Run test suite
    suite = ZeroHitTestSuite(args.segment, verbose=args.verbose)
    report = suite.run_suite()

    # Print summary
    suite.print_summary(report)

    # Save report if output specified
    if args.output:
        if args.format in ("markdown", "md"):
            save_markdown_report(report, args.output)
        else:
            save_json_report(report, args.output)

    # Exit with non-zero if high zero-hit ratio
    if report.zero_hit_ratio > 50:
        print("⚠️  WARNING: Zero-hit ratio is > 50%")
        sys.exit(1)

    print("✅ Test suite completed successfully!")


if __name__ == "__main__":
    main()
