#!/usr/bin/env python3
"""Telemetry Diagnostic Script - Generate reproducible reports.

Usage:
    python3 scripts/telemetry_diagnostic.py --segment /path/to/segment
    python3 scripts/telemetry_diagnostic.py --segment . --output docs/plans/telemetry_before.md
"""

import argparse
import json
from collections import Counter
from pathlib import Path


def classify_query_type(query: str) -> str:
    """Heurística de clasificación de query."""
    if not query:
        return "unknown"
    q_lower = query.lower()

    # Meta: qué hacer / estado / guía / arquitectura / procedimiento
    meta_keywords = [
        "how",
        "what",
        "where",
        "plan",
        "guide",
        "architecture",
        "design",
        "status",
        "overview",
        "explain",
        "description",
    ]

    # Impl: código específico / símbolos / funciones / archivos
    impl_keywords = [
        "function",
        "class",
        "method",
        "file",
        "implement",
        "code",
        "symbol",
        "def ",
        "class ",
        "import",
    ]

    if any(kw in q_lower for kw in impl_keywords):
        return "impl"
    elif any(kw in q_lower for kw in meta_keywords):
        return "meta"
    else:
        return "unknown"


def classify_hit_target(chunk_id: str) -> str:
    """Clasificar target por chunk_id prefix."""
    if not chunk_id:
        return "other"
    if chunk_id.startswith("skill:"):
        return "skill"
    elif chunk_id.startswith("prime:"):
        return "prime"
    elif chunk_id.startswith("session:"):
        return "session"
    elif chunk_id.startswith("agent:"):
        return "agent"
    elif chunk_id.startswith("ref:"):
        return "ref"
    else:
        return "other"


def generate_diagnostic(segment_path: Path) -> dict:
    """Generate diagnostic statistics from telemetry."""
    events_path = segment_path / "_ctx" / "telemetry" / "events.jsonl"

    events = []
    if events_path.exists():
        with open(events_path) as f:
            for line in f:
                if line.strip():
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass

    # Filter searches
    searches = [e for e in events if e["cmd"] == "ctx.search"]
    total_searches = len(searches)
    hits = sum(1 for e in searches if e.get("result", {}).get("hits", 0) > 0)
    zero_hits = total_searches - hits
    hit_rate = hits / total_searches * 100 if total_searches > 0 else 0
    latencies = [
        e.get("timing_ms", 0) for e in searches if e.get("timing_ms", 0) > 0
    ]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0

    # Top zero-hit queries
    zero_hit_queries = [
        (e.get("args", {}).get("query", ""), e.get("args", {}).get("query", ""))
        for e in searches
        if e.get("result", {}).get("hits", 0) == 0
    ]
    query_counts = Counter(q for q, _ in zero_hit_queries)

    # Breakdown por query_type
    query_type_counts = Counter()
    for e in searches:
        query = e.get("args", {}).get("query", "")
        qtype = classify_query_type(query)
        query_type_counts[qtype] += 1

    # Breakdown por hit_target
    hit_target_counts = Counter()
    for e in searches:
        returned_ids = e.get("result", {}).get("returned_ids", [])
        if returned_ids:
            for cid in returned_ids:
                target = classify_hit_target(cid)
                hit_target_counts[target] += 1

    return {
        "summary": {
            "total_searches": total_searches,
            "hits": hits,
            "zero_hits": zero_hits,
            "hit_rate": hit_rate,
            "avg_latency_ms": avg_latency,
        },
        "top_zero_hit_queries": [
            {"query": q, "count": c} for q, c in query_counts.most_common(10)
        ],
        "query_type_breakdown": dict(query_type_counts),
        "hit_target_breakdown": dict(hit_target_counts),
    }


def print_report(data: dict) -> None:
    """Print diagnostic report to stdout."""
    summary = data["summary"]

    print("=" * 60)
    print("DIAGNÓSTICO DE TELEMETRÍA")
    print("=" * 60)
    print()
    print("Resumen General")
    print("-" * 60)
    print(f"  total_searches:      {summary['total_searches']}")
    print(f"  hits:                {summary['hits']}")
    print(f"  zero_hits:           {summary['zero_hits']}")
    print(f"  hit_rate:            {summary['hit_rate']:.1f}%")
    print(f"  avg_latency_ms:      {summary['avg_latency_ms']:.1f}")
    print()

    print("Top Zero-Hit Queries (Top 10)")
    print("-" * 60)
    for item in data["top_zero_hit_queries"]:
        print(f"  [{item['count']:2d}] {item['query'][:60]}")
    print()

    print("Breakdown por Query Type")
    print("-" * 60)
    total = sum(data["query_type_breakdown"].values())
    for qtype, count in data["query_type_breakdown"].items():
        pct = count / total * 100 if total > 0 else 0
        print(f"  {qtype:<10} {count:>3}  ({pct:>5.1f}%)")
    print()

    if data["hit_target_breakdown"]:
        print("Breakdown por Hit Target")
        print("-" * 60)
        total_hits = sum(data["hit_target_breakdown"].values())
        for target, count in data["hit_target_breakdown"].items():
            pct = count / total_hits * 100 if total_hits > 0 else 0
            print(f"  {target:<10} {count:>3}  ({pct:>5.1f}%)")
        print()

    print("Heurística de Clasificación (Query Type)")
    print("-" * 60)
    print("  meta:     how/what/where/plan/guide/architecture/design/status")
    print("  impl:     function/class/method/file/implement/code/symbol")
    print("  unknown:  no clasificable")
    print()


def save_markdown(data: dict, output_path: Path) -> None:
    """Save diagnostic report as markdown."""
    summary = data["summary"]

    md = []
    md.append("# Telemetry Diagnostic Report")
    md.append("")
    md.append("## Resumen General")
    md.append("")
    md.append("| Métrica | Valor |")
    md.append("|---------|-------|")
    md.append(f"| total_searches | {summary['total_searches']} |")
    md.append(f"| hits | {summary['hits']} |")
    md.append(f"| zero_hits | {summary['zero_hits']} |")
    md.append(f"| hit_rate | {summary['hit_rate']:.1f}% |")
    md.append(f"| avg_latency_ms | {summary['avg_latency_ms']:.1f} |")
    md.append("")

    md.append("## Top Zero-Hit Queries (Top 10)")
    md.append("")
    md.append("| Count | Query |")
    md.append("|-------|-------|")
    for item in data["top_zero_hit_queries"]:
        md.append(f"| {item['count']} | {item['query'][:60]} |")
    md.append("")

    md.append("## Breakdown por Query Type")
    md.append("")
    md.append("| Type | Count | % |")
    md.append("|------|-------|---|")
    total = sum(data["query_type_breakdown"].values())
    for qtype, count in data["query_type_breakdown"].items():
        pct = count / total * 100 if total > 0 else 0
        md.append(f"| {qtype} | {count} | {pct:.1f}% |")
    md.append("")

    if data["hit_target_breakdown"]:
        md.append("## Breakdown por Hit Target")
        md.append("")
        md.append("| Target | Count | % |")
        md.append("|--------|-------|---|")
        total_hits = sum(data["hit_target_breakdown"].values())
        for target, count in data["hit_target_breakdown"].items():
            pct = count / total_hits * 100 if total_hits > 0 else 0
            md.append(f"| {target} | {count} | {pct:.1f}% |")
        md.append("")

    md.append("## Heurística de Clasificación")
    md.append("")
    md.append("### Query Type")
    md.append("- **meta**: how/what/where/plan/guide/architecture/design/status")
    md.append("- **impl**: function/class/method/file/implement/code/symbol")
    md.append("- **unknown**: no clasificable")
    md.append("")

    output_path.write_text("\n".join(md))


def main():
    parser = argparse.ArgumentParser(description="Generate telemetry diagnostic report")
    parser.add_argument(
        "--segment",
        "-s",
        type=Path,
        default=Path("."),
        help="Path to segment directory",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output path for markdown report (optional)",
    )
    parser.add_argument(
        "--json", action="store_true", help="Output JSON instead of text"
    )

    args = parser.parse_args()

    data = generate_diagnostic(args.segment)

    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print_report(data)

    if args.output:
        save_markdown(data, args.output)
        print(f"Report saved to: {args.output}")


if __name__ == "__main__":
    main()
