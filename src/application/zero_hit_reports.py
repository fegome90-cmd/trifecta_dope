"""Zero-hit ratio report generation with source segmentation.

B0 Instrumentation: Report zero-hit rates segmented by source (test/fixture/interactive/agent)
and build SHA to enable precise measurement of zero-hit reduction interventions.
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict


def generate_zero_hit_report(
    segment_path: Path, days: int = 30, output_path: Optional[Path] = None
) -> str:
    """Generate zero-hit ratio report segmented by source and build.

    Args:
        segment_path: Path to segment with telemetry
        days: Number of days to look back
        output_path: Optional path to write report

    Returns:
        Markdown formatted report
    """
    events_path = segment_path / "_ctx" / "telemetry" / "events.jsonl"

    if not events_path.exists():
        return "# Zero-Hit Report\n\nNo telemetry data found."

    # Parse events
    events = []
    with open(events_path) as f:
        for line in f:
            if line.strip():
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    # Filter to ctx.search events within time window
    from datetime import timezone

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    def parse_ts(ts_str):
        """Parse timestamp string, handling both offset-aware and naive."""
        if not ts_str:
            return datetime(2000, 1, 1, tzinfo=timezone.utc)
        # Handle Z suffix (UTC)
        if ts_str.endswith("Z"):
            ts_str = ts_str[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(ts_str)
            # If naive, assume UTC
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            return datetime(2000, 1, 1, tzinfo=timezone.utc)

    search_events = [
        e for e in events if e.get("cmd") == "ctx.search" and parse_ts(e.get("ts")) > cutoff
    ]

    # Aggregate by source
    by_source = defaultdict(lambda: {"total": 0, "zero_hits": 0, "reasons": defaultdict(int)})
    by_build = defaultdict(lambda: {"total": 0, "zero_hits": 0})

    for event in search_events:
        # Get source from extended fields (x) or default to "unknown"
        x = event.get("x", {})
        source = x.get("source", "unknown")
        build_sha = x.get("build_sha", "unknown")

        hits = event.get("result", {}).get("hits", 0)

        by_source[source]["total"] += 1
        by_build[build_sha]["total"] += 1

        if hits == 0:
            by_source[source]["zero_hits"] += 1
            by_build[build_sha]["zero_hits"] += 1

            # Track zero-hit reason
            reason = x.get("zero_hit_reason", "unknown")
            by_source[source]["reasons"][reason] += 1

    # Generate report
    lines = [
        "# Zero-Hit Ratio Report",
        f"\nGenerated: {datetime.now().isoformat()}",
        f"Period: Last {days} days",
        f"Total searches: {len(search_events)}\n",
        "## By Source",
        "",
        "| Source | Total | Zero Hits | Ratio |",
        "|--------|-------|-----------|-------|",
    ]

    for source in sorted(by_source.keys()):
        data = by_source[source]
        ratio = (data["zero_hits"] / data["total"] * 100) if data["total"] > 0 else 0
        lines.append(f"| {source} | {data['total']} | {data['zero_hits']} | {ratio:.1f}% |")

    lines.extend(
        [
            "",
            "## Zero-Hit Reasons by Source",
            "",
        ]
    )

    for source in sorted(by_source.keys()):
        data = by_source[source]
        if data["reasons"]:
            lines.append(f"### {source}")
            lines.append("")
            lines.append("| Reason | Count | % of Zero Hits |")
            lines.append("|--------|-------|----------------|")

            total_zero = data["zero_hits"]
            for reason, count in sorted(data["reasons"].items(), key=lambda x: -x[1]):
                pct = (count / total_zero * 100) if total_zero > 0 else 0
                lines.append(f"| {reason} | {count} | {pct:.1f}% |")
            lines.append("")

    lines.extend(
        [
            "## By Build",
            "",
            "| Build SHA | Total | Zero Hits | Ratio |",
            "|-----------|-------|-----------|-------|",
        ]
    )

    # Sort by most recent builds (assuming SHA order correlates with time)
    for build_sha in sorted(by_build.keys(), reverse=True)[:10]:
        data = by_build[build_sha]
        ratio = (data["zero_hits"] / data["total"] * 100) if data["total"] > 0 else 0
        lines.append(f"| {build_sha} | {data['total']} | {data['zero_hits']} | {ratio:.1f}% |")

    report = "\n".join(lines)

    if output_path:
        output_path.write_text(report)

    return report


def get_zero_hit_metrics(segment_path: Path, days: int = 30) -> Dict:
    """Get zero-hit metrics as dictionary for programmatic use.

    Args:
        segment_path: Path to segment with telemetry
        days: Number of days to look back

    Returns:
        Dictionary with metrics by source and overall
    """
    events_path = segment_path / "_ctx" / "telemetry" / "events.jsonl"

    if not events_path.exists():
        return {"error": "No telemetry data"}

    events = []
    with open(events_path) as f:
        for line in f:
            if line.strip():
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    def parse_ts(ts_str):
        if not ts_str:
            return datetime(2000, 1, 1, tzinfo=timezone.utc)
        if ts_str.endswith("Z"):
            ts_str = ts_str[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(ts_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            return datetime(2000, 1, 1, tzinfo=timezone.utc)

    search_events = [
        e for e in events if e.get("cmd") == "ctx.search" and parse_ts(e.get("ts")) > cutoff
    ]

    by_source = defaultdict(lambda: {"total": 0, "zero_hits": 0})

    for event in search_events:
        x = event.get("x", {})
        source = x.get("source", "unknown")
        hits = event.get("result", {}).get("hits", 0)

        by_source[source]["total"] += 1
        if hits == 0:
            by_source[source]["zero_hits"] += 1

    total = len(search_events)
    total_zero = sum(s["zero_hits"] for s in by_source.values())
    overall_ratio = (total_zero / total * 100) if total > 0 else 0

    return {
        "period_days": days,
        "total_searches": total,
        "total_zero_hits": total_zero,
        "overall_ratio": round(overall_ratio, 2),
        "by_source": {
            source: {
                "total": data["total"],
                "zero_hits": data["zero_hits"],
                "ratio": round(data["zero_hits"] / data["total"] * 100, 2)
                if data["total"] > 0
                else 0,
            }
            for source, data in by_source.items()
        },
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        segment = Path(sys.argv[1])
    else:
        segment = Path(".")

    report = generate_zero_hit_report(segment)
    print(report)
