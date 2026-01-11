#!/usr/bin/env python3
"""
Extract anchor usage metrics from Field Exercises telemetry.

Reads _ctx/telemetry/events.jsonl and extracts linter-related metrics
for WO-0010 Field Exercises evaluation.
"""

import json
import sys
from pathlib import Path
from typing import Any


def load_telemetry_events(events_path: Path) -> list[dict[str, Any]]:
    """Load telemetry events from JSONL file."""
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
                # Skip malformed lines
                continue
    return events


def extract_anchor_metrics(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Extract anchor usage metrics from ctx.search events."""

    # Filter to ctx.search events only (use 'cmd' field, not 'event_type')
    search_events = [e for e in events if e.get("cmd") == "ctx.search"]

    if not search_events:
        return {
            "error": "No ctx.search events found in telemetry",
            "total_events": len(events),
            "hint": "Check that evaluation was run with CLI (uv run trifecta ctx search)",
        }

    # Separate OFF (linter disabled) and ON (linter enabled) events
    # Linter metrics are in 'args' field, not top-level
    off_events = []
    on_events = []

    for e in search_events:
        args = e.get("args", {})
        # Check if linter was active via presence of linter_ fields
        if args.get("linter_expanded") is not None:
            on_events.append(e)
        else:
            off_events.append(e)

    # Metrics for ON mode (linter enabled)
    on_metrics = (
        analyze_linter_events(on_events) if on_events else {"error": "No ON mode events found"}
    )

    # Metrics for OFF mode (baseline)
    off_metrics = {
        "total_queries": len(off_events),
        "total_hits": sum(e.get("result", {}).get("hits", 0) for e in off_events),
        "avg_hits": (sum(e.get("result", {}).get("hits", 0) for e in off_events) / len(off_events))
        if off_events
        else 0,
        "zero_hit_count": sum(1 for e in off_events if e.get("result", {}).get("hits", 0) == 0),
    }

    return {
        "off_mode": off_metrics,
        "on_mode": on_metrics,
        "total_search_events": len(search_events),
        "off_events_count": len(off_events),
        "on_events_count": len(on_events),
    }


def analyze_linter_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze linter-specific metrics from ON mode events."""

    if not events:
        return {"error": "No ON mode events found"}

    # Count queries where linter expanded (check args field)
    expanded_count = sum(1 for e in events if e.get("args", {}).get("linter_expanded", False))

    # Count strong/weak anchors added
    total_strong = sum(e.get("args", {}).get("linter_added_strong_count", 0) for e in events)
    total_weak = sum(e.get("args", {}).get("linter_added_weak_count", 0) for e in events)

    # Query class distribution
    query_classes = {}
    for e in events:
        qclass = e.get("args", {}).get("linter_query_class", "unknown")
        query_classes[qclass] = query_classes.get(qclass, 0) + 1

    # Hits analysis (from result field)
    total_hits = sum(e.get("result", {}).get("hits", 0) for e in events)
    zero_hit_count = sum(1 for e in events if e.get("result", {}).get("hits", 0) == 0)

    # Hits when expanded vs not expanded
    expanded_events = [e for e in events if e.get("args", {}).get("linter_expanded", False)]
    not_expanded_events = [e for e in events if not e.get("args", {}).get("linter_expanded", False)]

    avg_hits_when_expanded = (
        (sum(e.get("result", {}).get("hits", 0) for e in expanded_events) / len(expanded_events))
        if expanded_events
        else 0
    )
    avg_hits_when_not_expanded = (
        (
            sum(e.get("result", {}).get("hits", 0) for e in not_expanded_events)
            / len(not_expanded_events)
        )
        if not_expanded_events
        else 0
    )

    return {
        "total_queries": len(events),
        "total_hits": total_hits,
        "avg_hits": total_hits / len(events),
        "zero_hit_count": zero_hit_count,
        "zero_hit_rate": (zero_hit_count / len(events)) * 100,
        # Anchor expansion metrics
        "anchor_usage_count": expanded_count,
        "anchor_usage_rate": (expanded_count / len(events)) * 100,
        "total_strong_anchors_added": total_strong,
        "total_weak_anchors_added": total_weak,
        "avg_strong_per_query": total_strong / len(events),
        "avg_weak_per_query": total_weak / len(events),
        # Query class distribution
        "query_class_distribution": query_classes,
        # Performance impact
        "avg_hits_when_expanded": avg_hits_when_expanded,
        "avg_hits_when_not_expanded": avg_hits_when_not_expanded,
        "delta_hits_when_expanded": avg_hits_when_expanded - avg_hits_when_not_expanded,
    }


def main() -> int:
    """Main extraction logic."""
    repo_root = Path(__file__).resolve().parents[2]
    telemetry_path = repo_root / "_ctx" / "telemetry" / "events.jsonl"
    output_path = repo_root / "_ctx" / "metrics" / "field_exercises_v1_anchor_metrics.json"

    if not telemetry_path.exists():
        print(f"❌ Telemetry file not found: {telemetry_path}")
        return 1

    print(f"📊 Loading telemetry from {telemetry_path}...")
    events = load_telemetry_events(telemetry_path)
    print(f"   Loaded {len(events)} events")

    print("🔍 Extracting anchor metrics...")
    metrics = extract_anchor_metrics(events)

    # Check for errors
    if "error" in metrics:
        print(f"❌ {metrics['error']}")
        if "hint" in metrics:
            print(f"   ℹ️  {metrics['hint']}")
        print(f"   Total events: {metrics.get('total_events', 0)}")
        return 1

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"✅ Metrics written to {output_path}")
    print(f"\n📈 Summary:")
    print(
        f"   OFF mode: {metrics['off_mode']['total_queries']} queries, {metrics['off_mode']['avg_hits']:.2f} avg hits"
    )
    print(
        f"   ON mode:  {metrics['on_mode']['total_queries']} queries, {metrics['on_mode']['avg_hits']:.2f} avg hits"
    )
    print(
        f"   Anchor usage: {metrics['on_mode']['anchor_usage_count']}/{metrics['on_mode']['total_queries']} ({metrics['on_mode']['anchor_usage_rate']:.1f}%)"
    )
    print(f"   Delta when expanded: {metrics['on_mode']['delta_hits_when_expanded']:+.2f} hits")

    return 0


if __name__ == "__main__":
    sys.exit(main())
