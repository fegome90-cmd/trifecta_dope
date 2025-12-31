"""Telemetry Report Generation.

Generate concise reports from Trifecta telemetry data.
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from collections import Counter


def load_telemetry_data(segment_path: Path) -> tuple[List[Dict], Dict, Dict]:
    """Load telemetry data from segment.

    Args:
        segment_path: Path to segment directory

    Returns:
        Tuple of (events, metrics, last_run)
    """
    tel_dir = segment_path / "_ctx" / "telemetry"

    events = []
    events_path = tel_dir / "events.jsonl"
    if events_path.exists():
        with open(events_path) as f:
            for line in f:
                if line.strip():
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass

    metrics = {}
    metrics_path = tel_dir / "metrics.json"
    if metrics_path.exists():
        try:
            metrics = json.loads(metrics_path.read_text())
        except json.JSONDecodeError:
            pass

    last_run = {}
    last_run_path = tel_dir / "last_run.json"
    if last_run_path.exists():
        try:
            last_run = json.loads(last_run_path.read_text())
        except json.JSONDecodeError:
            pass

    return events, metrics, last_run


def filter_events_by_date(events: List[Dict], days: int) -> List[Dict]:
    """Filter events to last N days.

    Args:
        events: List of event dictionaries
        days: Number of days to look back

    Returns:
        Filtered events list
    """
    if days <= 0:
        return events

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    filtered = []

    for event in events:
        try:
            ts = datetime.fromisoformat(event["ts"].replace("Z", "+00:00"))
            if ts >= cutoff:
                filtered.append(event)
        except (KeyError, ValueError):
            # Include events with invalid timestamps
            filtered.append(event)

    return filtered


def generate_report(
    segment_path: Path,
    last_days: int = 7,
    format_type: str = "table"
) -> str:
    """Generate telemetry report.

    Args:
        segment_path: Path to segment directory
        last_days: Number of days to include (0 = all)
        format_type: Output format ("table" or "json")

    Returns:
        Formatted report string
    """
    events, metrics, last_run = load_telemetry_data(segment_path)

    if not events and not metrics:
        return "No telemetry data found."

    # Filter by date
    if last_days > 0:
        events = filter_events_by_date(events, last_days)

    if format_type == "json":
        return json.dumps({
            "events": events,
            "metrics": metrics,
            "last_run": last_run
        }, indent=2)

    # Generate table report
    lines = []
    lines.append("╭" + "─" * 50 + "╮")
    lines.append("│" + " " * 15 + "Trifecta Telemetry Report" + " " * 13 + "│")
    lines.append(f"│              Last {last_days} days" + " " * 25 + "│")
    lines.append("╰" + "─" * 50 + "╯")
    lines.append("")

    # Summary
    total_commands = len(events)
    cmd_counts = Counter(e["cmd"] for e in events)
    unique_sessions = len(set(e.get("run_id", "") for e in events))

    # Calculate average latency
    latencies = [e.get("timing_ms", 0) for e in events if e.get("timing_ms", 0) > 0]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0

    # Calculate token metrics
    total_tokens = sum(e.get("tokens", {}).get("total_tokens", 0) for e in events)
    avg_tokens = total_tokens / total_commands if total_commands > 0 else 0
    total_retrieved = sum(e.get("tokens", {}).get("retrieved_tokens", 0) for e in events)

    lines.append("Summary")
    lines.append("─" * 50)
    lines.append(f"  Total commands:      {total_commands}")
    lines.append(f"  Unique sessions:     {unique_sessions}")
    lines.append(f"  Avg latency:         {avg_latency:.1f}ms")
    lines.append(f"  Total tokens:        {total_tokens:,}")
    lines.append(f"  Avg tokens/call:     {avg_tokens:.0f}")
    lines.append(f"  Retrieved tokens:    {total_retrieved:,}")
    lines.append("")

    # Top commands
    lines.append("Top Commands")
    lines.append("─" * 50)
    for cmd, count in cmd_counts.most_common(5):
        pct = count / total_commands * 100 if total_commands > 0 else 0
        lines.append(f"  {cmd:<20} {count:>3}  ({pct:>5.1f}%)")
    lines.append("")

    # Search effectiveness
    searches = [e for e in events if e["cmd"] == "ctx.search"]
    if searches:
        total_searches = len(searches)
        with_hits = sum(1 for e in searches if e.get("result", {}).get("hits", 0) > 0)
        zero_hits = total_searches - with_hits
        hit_rate = with_hits / total_searches * 100 if total_searches > 0 else 0

        lines.append("Search Effectiveness")
        lines.append("─" * 50)
        lines.append(f"  Total searches:      {total_searches}")
        lines.append(f"  With hits:           {with_hits}  ({hit_rate:.1f}%)")
        lines.append(f"  Zero hits:           {zero_hits}  ({100-hit_rate:.1f}%)")

        if zero_hits > total_searches * 0.5:
            lines.append(f"  ⚠️  High zero-hit rate")

    lines.append("")

    # Token efficiency by command
    lines.append("Token Efficiency")
    lines.append("─" * 50)
    cmd_token_stats: Dict[str, Dict] = {}
    for e in events:
        cmd = e["cmd"]
        tokens = e.get("tokens", {})
        if cmd not in cmd_token_stats:
            cmd_token_stats[cmd] = {"count": 0, "tokens": 0}
        cmd_token_stats[cmd]["count"] += 1
        cmd_token_stats[cmd]["tokens"] += tokens.get("total_tokens", 0)

    for cmd, stats in sorted(cmd_token_stats.items(), key=lambda x: x[1]["tokens"] / x[1]["count"] if x[1]["count"] > 0 else 0):
        avg_t = stats["tokens"] / stats["count"] if stats["count"] > 0 else 0
        lines.append(f"  {cmd:<20} {avg_t:>6.0f} avg tokens")
    lines.append("")

    return "\n".join(lines)


def export_data(
    segment_path: Path,
    format_type: str = "json",
    output_path: Optional[Path] = None
) -> str:
    """Export telemetry data.

    Args:
        segment_path: Path to segment directory
        format_type: Export format ("json" or "csv")
        output_path: Optional file to write to

    Returns:
        Exported data string
    """
    events, metrics, last_run = load_telemetry_data(segment_path)

    if format_type == "csv":
        # Export as CSV
        if not events:
            return ""

        headers = ["timestamp", "command", "timing_ms", "status"]
        lines = [",".join(headers)]

        for event in events:
            timestamp = event.get("ts", "")
            command = event.get("cmd", "")
            timing = event.get("timing_ms", 0)
            status = event.get("result", {}).get("status", "unknown")
            lines.append(f'"{timestamp}",{command},{timing},{status}')

        data = "\n".join(lines)
    else:
        # Export as JSON
        data = json.dumps({
            "events": events,
            "metrics": metrics,
            "last_run": last_run,
            "exported_at": datetime.now(timezone.utc).isoformat()
        }, indent=2)

    if output_path:
        output_path.write_text(data)

    return data


def get_quick_stats(segment_path: Path) -> Dict[str, Any]:
    """Get quick stats for summary display.

    Args:
        segment_path: Path to segment directory

    Returns:
        Dictionary with quick stats
    """
    events, metrics, last_run = load_telemetry_data(segment_path)

    cmd_counts = Counter(e["cmd"] for e in events)
    searches = [e for e in events if e["cmd"] == "ctx.search"]
    with_hits = sum(1 for e in searches if e.get("result", {}).get("hits", 0) > 0)

    return {
        "total_commands": len(events),
        "total_searches": len(searches),
        "searches_with_hits": with_hits,
        "hit_rate": with_hits / len(searches) if searches else 0,
        "top_command": cmd_counts.most_common(1)[0] if cmd_counts else None,
    }
