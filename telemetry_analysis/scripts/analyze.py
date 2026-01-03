#!/usr/bin/env python3
"""
Trifecta Telemetry Analyzer

Genera análisis básico de telemetría de un segmento Trifecta.

Uso:
    python analyze.py <segment_path>
    python analyze.py .                    # Segmento actual
    python analyze.py /ruta/al/segmento   # Segmento específico
"""

import argparse
import json
from pathlib import Path
from collections import Counter
from datetime import datetime


def load_telemetry(segment_path: Path):
    """Carga archivos de telemetría."""
    tel_dir = segment_path / "_ctx" / "telemetry"

    events = []
    if (tel_dir / "events.jsonl").exists():
        with open(tel_dir / "events.jsonl") as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))

    metrics = {}
    if (tel_dir / "metrics.json").exists():
        metrics = json.loads((tel_dir / "metrics.json").read_text())

    last_run = {}
    if (tel_dir / "last_run.json").exists():
        last_run = json.loads((tel_dir / "last_run.json").read_text())

    return events, metrics, last_run


def executive_summary(events, metrics, last_run):
    """Genera Executive Summary."""
    print("\n" + "=" * 60)
    print("EXECUTIVE SUMMARY")
    print("=" * 60)

    # Total commands
    cmd_counts = Counter(e["cmd"] for e in events)
    total = len(events)

    print(f"\n📊 Commands: {total} total")
    for cmd, count in cmd_counts.most_common():
        pct = count / total * 100 if total > 0 else 0
        print(f"   - {cmd}: {count} ({pct:.1f}%)")

    # Latencies
    if last_run.get("latencies"):
        print("\n⚡ Latency:")
        for cmd, stats in last_run["latencies"].items():
            print(f"   - {cmd}: P50={stats['p50_ms']}ms, P95={stats['p95_ms']}ms")

    # Errors
    errors = [e for e in events if e.get("result", {}).get("status") != "ok"]
    if errors:
        print(f"\n⚠️  Errors: {len(errors)}")
        err_types = Counter(e.get("result", {}).get("status", "unknown") for e in errors)
        for err_type, count in err_types.most_common(5):
            print(f"   - {err_type}: {count}")

    # Key Insight
    print("\n💡 Key Insight:")
    if metrics.get("ctx_search_count", 0) > 0:
        hit_rate = metrics.get("ctx_search_hits_total", 0) / metrics.get("ctx_search_count", 1)
        zero_hit_pct = metrics.get("ctx_search_zero_hits_count", 0) / metrics.get("ctx_search_count", 1) * 100
        print(f"   - Search hit rate: {hit_rate:.1%}")
        print(f"   - Zero-hit searches: {zero_hit_pct:.1f}%")

    if last_run.get("pack_state"):
        pack = last_run["pack_state"]
        print(f"   - Pack SHA: {pack.get('pack_sha', 'N/A')}")
        print(f"   - Pack stale: {pack.get('stale_detected', 'N/A')}")


def performance_analysis(events, metrics, last_run):
    """Genera Performance Analysis."""
    print("\n" + "=" * 60)
    print("PERFORMANCE ANALYSIS")
    print("=" * 60)

    # Latency Distribution
    if last_run.get("latencies"):
        print("\n📈 Latency Distribution:")
        for cmd, stats in sorted(last_run["latencies"].items()):
            print(f"\n   {cmd}:")
            print(f"      P50:  {stats['p50_ms']}ms")
            print(f"      P95:  {stats['p95_ms']}ms")
            print(f"      Max:  {stats['max_ms']}ms")
            print(f"      Count: {stats['count']}")

    # Search Effectiveness
    if metrics.get("ctx_search_count"):
        total_search = metrics["ctx_search_count"]
        hits = metrics.get("ctx_search_hits_total", 0)
        zero_hits = metrics.get("ctx_search_zero_hits_count", 0)

        print("\n🔍 Search Effectiveness:")
        print(f"   - Total searches: {total_search}")
        print(f"   - Total hits: {hits}")
        print(f"   - Zero-hit: {zero_hits} ({zero_hits/total_search*100:.1f}%)")

        # Top queries (if available)
        search_events = [e for e in events if e["cmd"] == "ctx.search"]
        if search_events:
            queries = [e.get("args", {}).get("query", "") for e in search_events]
            print(f"   - Unique queries: {len(set(queries))}")

    # Pack State
    if last_run.get("pack_state"):
        pack = last_run["pack_state"]
        print("\n📦 Pack State:")
        print(f"   - SHA: {pack.get('pack_sha', 'N/A')}")
        if pack.get('pack_mtime'):
            mtime = datetime.fromtimestamp(pack['pack_mtime'])
            print(f"   - Modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   - Stale detected: {pack.get('stale_detected', 'N/A')}")


def main():
    parser = argparse.ArgumentParser(description="Analyze Trifecta telemetry")
    parser.add_argument("segment", nargs="?", default=".", help="Segment path (default: current dir)")
    parser.add_argument("--report", choices=["executive", "performance", "full"],
                      default="full", help="Report type")
    args = parser.parse_args()

    segment_path = Path(args.segment).resolve()

    if not (segment_path / "_ctx" / "telemetry").exists():
        print(f"Error: No telemetry found in {segment_path}")
        return 1

    events, metrics, last_run = load_telemetry(segment_path)

    if not events:
        print("No events found in telemetry.")
        return 0

    if args.report in ["executive", "full"]:
        executive_summary(events, metrics, last_run)

    if args.report in ["performance", "full"]:
        performance_analysis(events, metrics, last_run)

    print("\n" + "=" * 60 + "\n")

    return 0


if __name__ == "__main__":
    exit(main())
