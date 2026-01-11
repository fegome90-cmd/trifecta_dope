#!/usr/bin/env python3
"""
Field Exercises v2 - Causal Metrics Calculator

Computes:
- anchor_usage_rate_on per bucket
- zero_hit_rate_on per bucket
- median(delta_hits) for expanded=true vs expanded=false
"""

import json
import statistics
import sys
from pathlib import Path
from typing import Any


def calculate_causal_metrics(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate causal metrics from A/B results."""

    # Group by bucket
    buckets = {}
    for r in results:
        bucket = r["bucket"]
        if bucket not in buckets:
            buckets[bucket] = []
        buckets[bucket].append(r)

    # Calculate per-bucket metrics
    bucket_metrics = {}
    for bucket_name, items in buckets.items():
        total = len(items)
        if total == 0:
            continue

        # Metrics - Strict calculation from data
        hits_on = [item["on"]["hits"] for item in items if item["on"]["returncode"] == 0]
        # Zero hit count: count of queries where hits == 0
        zero_hit_count = sum(1 for h in hits_on if h == 0)

        # Anchor usage: Check telemetry
        # Note: telemetry dict might be missing if run failed, default to False
        anchor_count = sum(
            1 for item in items if item["on"].get("telemetry", {}).get("linter_expanded", False)
        )

        # Invariant checks
        median_hits = statistics.median(hits_on) if hits_on else 0
        if zero_hit_count == total and median_hits > 0:
            # This should be mathematically impossible if all are 0
            raise ValueError(
                f"Invariant Violation in bucket '{bucket_name}': 100% zero-hits but median is {median_hits}"
            )

        bucket_metrics[bucket_name] = {
            "total_queries": total,
            "anchor_usage_count": anchor_count,
            "anchor_usage_rate": round((anchor_count / total) * 100, 1),
            "zero_hit_count": zero_hit_count,
            "zero_hit_rate": round((zero_hit_count / total) * 100, 1),
            "median_hits_on": median_hits,
            "mean_hits_on": statistics.mean(hits_on) if hits_on else 0,
        }

    # Calculate delta_hits
    deltas_expanded = []
    deltas_not_expanded = []

    for r in results:
        delta = r["on"]["hits"] - r["off"]["hits"]
        expanded = r["on"]["telemetry"].get("linter_expanded", False)

        if expanded:
            deltas_expanded.append(delta)
        else:
            deltas_not_expanded.append(delta)

    # Median deltas
    median_delta_expanded = statistics.median(deltas_expanded) if deltas_expanded else 0
    median_delta_not_expanded = statistics.median(deltas_not_expanded) if deltas_not_expanded else 0

    return {
        "buckets": bucket_metrics,
        "causal_deltas": {
            "expanded_true": {
                "count": len(deltas_expanded),
                "median_delta": median_delta_expanded,
                "deltas": deltas_expanded,
            },
            "expanded_false": {
                "count": len(deltas_not_expanded),
                "median_delta": median_delta_not_expanded,
                "deltas": deltas_not_expanded,
            },
        },
    }


def check_gates(metrics: dict[str, Any]) -> dict[str, Any]:
    """Check quality gates."""
    gates = {}

    # Gate 1: vague_1token anchor_usage_rate >= 30%
    vague_usage = metrics["buckets"].get("vague_1token", {}).get("anchor_usage_rate", 0)
    gates["vague_anchor_usage_30pct"] = {
        "value": vague_usage,
        "threshold": 30.0,
        "pass": vague_usage >= 30.0,
    }

    # Gate 2: vague_1token zero_hit_rate <= 20%
    vague_zero_hit = metrics["buckets"].get("vague_1token", {}).get("zero_hit_rate", 0)
    gates["vague_zero_hit_20pct"] = {
        "value": vague_zero_hit,
        "threshold": 20.0,
        "pass": vague_zero_hit <= 20.0,
    }

    # Gate 3: expanded=true median_delta > 0
    expanded_delta = metrics["causal_deltas"]["expanded_true"]["median_delta"]
    gates["expanded_positive_delta"] = {
        "value": expanded_delta,
        "threshold": 0.0,
        "pass": expanded_delta > 0.0,
    }

    # Overall gate
    overall_pass = all(g["pass"] for g in gates.values())

    return {
        "gates": gates,
        "overall_pass": overall_pass,
    }


def main() -> int:
    """Main metrics calculator."""
    repo_root = Path(__file__).resolve().parents[2]
    input_path = repo_root / "_ctx" / "metrics" / "field_exercises_v2_ab.json"
    output_path = repo_root / "_ctx" / "metrics" / "field_exercises_v2_summary.json"

    print("📊 Loading A/B results...")
    with open(input_path) as f:
        results = json.load(f)
    print(f"   Loaded {len(results)} queries")

    print("🔍 Calculating causal metrics...")
    metrics = calculate_causal_metrics(results)

    print("🚦 Checking gates...")
    gate_results = check_gates(metrics)

    # Combine
    output = {
        "metrics": metrics,
        "gate_results": gate_results,
    }

    # Write
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"✅ Summary written to {output_path}")
    print(f"\n📈 Results:")
    for bucket, stats in metrics["buckets"].items():
        print(f"   {bucket}:")
        print(f"      Anchor usage: {stats['anchor_usage_rate']:.1f}%")
        print(f"      Zero-hit rate: {stats['zero_hit_rate']:.1f}%")

    print(f"\n   Causal Deltas:")
    print(
        f"      Expanded=true: median Δ = {metrics['causal_deltas']['expanded_true']['median_delta']:+.1f}"
    )
    print(
        f"      Expanded=false: median Δ = {metrics['causal_deltas']['expanded_false']['median_delta']:+.1f}"
    )

    print(f"\n🚦 Gates:")
    for gate_name, gate_data in gate_results["gates"].items():
        status = "✅ PASS" if gate_data["pass"] else "❌ FAIL"
        print(
            f"   {gate_name}: {status} ({gate_data['value']:.1f} vs {gate_data['threshold']:.1f})"
        )

    print(f"\n{'✅ ALL GATES PASSED' if gate_results['overall_pass'] else '❌ GATES FAILED'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
