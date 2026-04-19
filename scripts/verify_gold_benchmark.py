#!/usr/bin/env python3
"""
Gold Benchmark Harness for Skill Hub Ranking.
Loads external dataset and verifies ranking quality using prefix-matching for IDs.
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Any, List

# Add src to path for direct imports
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(REPO_ROOT))

from src.application.context_service import ContextService

def clean_id(full_id: str) -> str:
    """Extract kind:name from kind:name:hash for stable matching."""
    parts = full_id.split(":")
    if len(parts) >= 2:
        return f"{parts[0]}:{parts[1]}"
    return full_id

def run_benchmark(segment_path: Path, dataset_path: Path, output_path: Path | None = None):
    print(f"🔍 Running Gold Benchmark")
    print(f"   Segment: {segment_path}")
    print(f"   Dataset: {dataset_path}")
    print("=" * 70)
    
    if not segment_path.exists():
        print(f"❌ Error: Segment path {segment_path} does not exist.")
        sys.exit(1)
    if not dataset_path.exists():
        print(f"❌ Error: Dataset path {dataset_path} does not exist.")
        sys.exit(1)

    with open(dataset_path, "r") as f:
        benchmark_cases = json.load(f)

    service = ContextService(segment_path)
    report = []

    for case in benchmark_cases:
        query = case["query"]
        print(f"\nQuery: '{query}' ({case['intent']})")
        
        try:
            search_result = service.search(query, k=5)
        except Exception as e:
            print(f"  ❌ Search failed: {e}")
            continue

        hits = search_result.hits
        if not hits:
            print("  ⚠️ No hits found.")
            report.append({**case, "status": "FAIL", "reason": "No hits"})
            continue

        # Analysis with clean IDs
        top_ids = [clean_id(h.id) for h in hits]
        top1 = top_ids[0]
        
        pass_top1 = top1 == case["expected_top1"]
        pass_top3 = pass_top1 or any(hid in case["acceptable_top3"] for hid in top_ids[:3])

        status_top1 = "✅" if pass_top1 else "❌"
        status_top3 = "✅" if pass_top3 else "❌"

        print(f"  Top-1: {status_top1} {top1} (Exp: {case['expected_top1']})")
        print(f"  Top-3: {status_top3} {', '.join(top_ids[:3])}")

        report.append({
            "query": query,
            "top1": top1,
            "top3": top_ids[:3],
            "pass_top1": pass_top1,
            "pass_top3": pass_top3,
            "expected_top1": case["expected_top1"],
            "acceptable_top3": case["acceptable_top3"],
            "all_hits": [{"id": clean_id(h.id), "score": h.score} for h in hits]
        })

    # Summary
    total = len(report)
    passed_top1 = sum(1 for r in report if r["pass_top1"])
    passed_top3 = sum(1 for r in report if r["pass_top3"])
    
    print("\n" + "=" * 70)
    print(f"SUMMARY: Top-1 Accuracy: {passed_top1}/{total} | Top-3 Recall: {passed_top3}/{total}")
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump({
                "summary": {"top1": passed_top1, "top3": passed_top3, "total": total},
                "results": report
            }, f, indent=2)
        print(f"Report saved to: {output_path}")

    return passed_top1 == total and passed_top3 == total

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--segment", type=Path, default=Path.home() / ".trifecta/segments/skills-hub")
    parser.add_argument("--dataset", type=Path, default=REPO_ROOT / "data/gold_benchmark_queries.json")
    parser.add_argument("--output", type=Path, default=REPO_ROOT / "docs/reports/SH-RANKING-001-baseline.json")
    args = parser.parse_args()

    success = run_benchmark(args.segment, args.dataset, args.output)
    sys.exit(0 if success else 1)
