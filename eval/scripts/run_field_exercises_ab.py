#!/usr/bin/env python3
"""
Field Exercises A/B Evaluation Runner

Usage:
  python eval/scripts/run_field_exercises_ab.py --validate
  python eval/scripts/run_field_exercises_ab.py --mode off --output _ctx/logs/field_ex_off.log
  python eval/scripts/run_field_exercises_ab.py --mode on --output _ctx/logs/field_ex_on.log
  python eval/scripts/run_field_exercises_ab.py --generate-report
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


def load_dataset(dataset_path: Path) -> dict[str, Any]:
    """Load field exercises dataset."""
    with open(dataset_path) as f:
        return yaml.safe_load(f)


def validate_dataset(dataset: dict[str, Any]) -> bool:
    """Validate dataset schema."""
    queries = dataset.get("queries", [])

    if len(queries) != 20:
        print(f"❌ Dataset must have exactly 20 queries, found {len(queries)}")
        return False

    for q in queries:
        required = ["id", "type", "query", "expected_min_hits", "rationale"]
        missing = [f for f in required if f not in q]
        if missing:
            print(f"❌ Query {q.get('id', 'UNKNOWN')} missing fields: {missing}")
            return False

        if q["type"] not in ["technical", "conceptual", "discovery"]:
            print(f"❌ Query {q['id']} has invalid type: {q['type']}")
            return False

    print(f"✅ Dataset valid: {len(queries)} queries")
    return True


def run_query_cli(query: str, mode: str, segment: Path) -> dict[str, Any]:
    """Execute query via CLI and parse results."""
    env = os.environ.copy()

    cmd = [
        "uv",
        "run",
        "trifecta",
        "ctx",
        "search",
        "--segment",
        str(segment),
        "--query",
        query,
        "--limit",
        "10",
    ]

    if mode == "off":
        cmd.append("--no-lint")
    elif mode == "on":
        env["TRIFECTA_LINT"] = "1"

    result = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=segment.parent)

    # Parse output to extract hit count
    # Look for "Search Results (X hits)" pattern
    hits = 0
    found_match = re.search(r"Search Results \((\d+) hits?\)", result.stdout)
    if found_match:
        hits = int(found_match.group(1))

    return {
        "hits": hits,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
    }


def run_evaluation(
    dataset: dict[str, Any], mode: str, segment: Path, output_path: Path | None = None
) -> list[dict]:
    """Run all queries in specified mode."""
    results = []
    queries = dataset["queries"]

    full_output = []

    print(f"Running {len(queries)} queries in mode={mode}...")

    for i, q in enumerate(queries, 1):
        query_id = q["id"]
        query_text = q["query"]

        print(f"  [{i}/{len(queries)}] {query_id}: {query_text[:50]}...")

        cli_result = run_query_cli(query_text, mode, segment)

        result = {
            "id": query_id,
            "type": q["type"],
            "query": query_text,
            "hits": cli_result["hits"],
            "expected_min_hits": q["expected_min_hits"],
            "returncode": cli_result["returncode"],
        }
        results.append(result)

        # Append to full output log
        full_output.append(f"=== {query_id} ===")
        full_output.append(f"Query: {query_text}")
        full_output.append(f"Mode: {mode}")
        full_output.append(f"Hits: {cli_result['hits']}")
        full_output.append(f"STDOUT:\n{cli_result['stdout']}")
        if cli_result["stderr"]:
            full_output.append(f"STDERR:\n{cli_result['stderr']}")
        full_output.append("\n")

    # Write full log
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(full_output))
        print(f"✅ Logs written to {output_path}")

    return results


def calculate_metrics(results: list[dict]) -> dict[str, Any]:
    """Calculate evaluation metrics."""
    total = len(results)
    zero_hits = sum(1 for r in results if r["hits"] == 0)
    total_hits = sum(r["hits"] for r in results)

    return {
        "total_queries": total,
        "zero_hit_count": zero_hits,
        "zero_hit_rate": (zero_hits / total) * 100 if total > 0 else 0,
        "avg_hits": total_hits / total if total > 0 else 0,
        "total_hits": total_hits,
    }


def generate_report(results_off: list[dict], results_on: list[dict], report_path: Path) -> None:
    """Generate markdown report."""
    metrics_off = calculate_metrics(results_off)
    metrics_on = calculate_metrics(results_on)

    delta_zero_rate = metrics_on["zero_hit_rate"] - metrics_off["zero_hit_rate"]
    delta_avg_hits = metrics_on["avg_hits"] - metrics_off["avg_hits"]

    gate_status = "✅ PASS" if metrics_on["zero_hit_rate"] < 30 else "❌ FAIL"

    # Find queries with 0 hits in ON mode
    zero_hit_queries_on = [r for r in results_on if r["hits"] == 0]

    # Find top performers
    top_performers = sorted(results_on, key=lambda r: r["hits"], reverse=True)[:5]

    report = f"""# Field Exercises v1 - Evaluation Results

**Date**: 2026-01-06  
**Dataset**: 20 real-world queries  
**Modes**: OFF (--no-lint) vs ON (TRIFECTA_LINT=1)

---

## Metrics

| Metric | OFF | ON | Delta |
|--------|-----|----|----- |
| Zero-hit rate | {metrics_off["zero_hit_rate"]:.1f}% | {metrics_on["zero_hit_rate"]:.1f}% | {delta_zero_rate:+.1f}% |
| Avg hits per query | {metrics_off["avg_hits"]:.2f} | {metrics_on["avg_hits"]:.2f} | {delta_avg_hits:+.2f} |
| Total hits | {metrics_off["total_hits"]} | {metrics_on["total_hits"]} | {metrics_on["total_hits"] - metrics_off["total_hits"]:+d} |
| Queries with 0 hits | {metrics_off["zero_hit_count"]}/20 | {metrics_on["zero_hit_count"]}/20 | {metrics_on["zero_hit_count"] - metrics_off["zero_hit_count"]:+d} |

---

## Gate Status

**Zero-hit rate ON**: {metrics_on["zero_hit_rate"]:.1f}%  
**Threshold**: < 30%  
**Status**: {gate_status}

---

## Query Breakdown

### Queries with 0 hits (ON mode)
"""

    if zero_hit_queries_on:
        for q in zero_hit_queries_on:
            report += f'\n- **{q["id"]}** ({q["type"]}): "{q["query"]}"'
    else:
        report += "\n✅ No queries with 0 hits!\n"

    report += "\n\n### Top Performers (ON mode)\n"
    for q in top_performers:
        report += f'\n- **{q["id"]}** ({q["type"]}): "{q["query"]}" → {q["hits"]} hits'

    report += f"""

---

## Recommendations

"""

    if metrics_on["zero_hit_rate"] < 30:
        report += (
            "✅ Search quality meets threshold. System is performing well on real-world queries.\n"
        )
    else:
        report += "⚠️ High zero-hit rate indicates search quality issues. Investigate:\n"
        report += "- Missing content in indexed files\n"
        report += "- Linter configuration gaps\n"
        report += "- Query normalization issues\n"

    if delta_avg_hits > 0:
        report += f"\n✅ Linter improves search: +{delta_avg_hits:.2f} avg hits per query\n"
    else:
        report += f"\n⚠️ Linter provides no improvement: {delta_avg_hits:.2f} delta\n"

    report += "\n---\n\n**END OF REPORT**\n"

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report)
    print(f"✅ Report written to {report_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Field Exercises A/B Evaluation")
    parser.add_argument("--validate", action="store_true", help="Validate dataset only")
    parser.add_argument("--mode", choices=["off", "on"], help="Evaluation mode")
    parser.add_argument("--output", type=Path, help="Output log path")
    parser.add_argument(
        "--generate-report", action="store_true", help="Generate report from cached results"
    )

    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    dataset_path = repo_root / "eval" / "field_exercises_v1.yaml"

    if not dataset_path.exists():
        print(f"❌ Dataset not found: {dataset_path}")
        return 1

    dataset = load_dataset(dataset_path)

    if args.validate:
        return 0 if validate_dataset(dataset) else 1

    if args.mode:
        if not args.output:
            print("❌ --output required with --mode")
            return 1

        results = run_evaluation(dataset, args.mode, repo_root, args.output)

        # Cache results
        cache_path = repo_root / f".cache_field_ex_{args.mode}.json"
        cache_path.write_text(json.dumps(results, indent=2))

        metrics = calculate_metrics(results)
        print(f"\nMetrics ({args.mode}):")
        print(f"  Zero-hit rate: {metrics['zero_hit_rate']:.1f}%")
        print(f"  Avg hits: {metrics['avg_hits']:.2f}")
        print(f"  Total hits: {metrics['total_hits']}")

        return 0

    if args.generate_report:
        cache_off = repo_root / ".cache_field_ex_off.json"
        cache_on = repo_root / ".cache_field_ex_on.json"

        if not cache_off.exists() or not cache_on.exists():
            print("❌ Run --mode off and --mode on first to generate caches")
            return 1

        results_off = json.loads(cache_off.read_text())
        results_on = json.loads(cache_on.read_text())

        report_path = repo_root / "docs" / "reports" / "field_exercises_v1_results.md"
        generate_report(results_off, results_on, report_path)

        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
