#!/usr/bin/env python3
"""
Grid Search Calibration for Skill Hub Ranking.
Finds the optimal hyperparameters for maximum Top-1 Accuracy.
"""

import sys
import json
from pathlib import Path
from typing import Any

# Add src to path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(REPO_ROOT))

from src.application.context_service import ContextService

# Search Space
C_VALUES = [10, 25, 50, 100, 200]
WEIGHT_VALUES = [2.0, 4.0, 6.0, 8.0]
PHRASE_VALUES = [2.0, 4.0]

DEFAULT_HUB_PATH = Path.home() / ".trifecta/segments/skills-hub"
DATASET_PATH = REPO_ROOT / "data/gold_benchmark_queries.json"

def clean_id(full_id: str) -> str:
    parts = full_id.split(":")
    return f"{parts[0]}:{parts[1]}" if len(parts) >= 2 else full_id

def evaluate(params: dict[str, float], segment_path: Path, cases: list[dict]):
    service = ContextService(segment_path, scoring_params=params)
    top1_hits = 0
    
    for case in cases:
        try:
            res = service.search(case["query"], k=1)
            if res.hits and clean_id(res.hits[0].id) == case["expected_top1"]:
                top1_hits += 1
        except:
            continue
            
    return (top1_hits / len(cases)) * 100

def main():
    print("🚀 Starting Ranking Calibration (Grid Search)")
    print(f"   Target: {DEFAULT_HUB_PATH}")
    print("-" * 50)

    if not DATASET_PATH.exists():
        print(f"❌ Error: Dataset not found at {DATASET_PATH}")
        sys.exit(1)

    with open(DATASET_PATH, "r") as f:
        cases = json.load(f)

    results = []
    
    for c in C_VALUES:
        for w in WEIGHT_VALUES:
            for p in PHRASE_VALUES:
                params = {
                    "norm_constant": float(c),
                    "identity_weight": float(w),
                    "phrase_boost": float(p)
                }
                accuracy = evaluate(params, DEFAULT_HUB_PATH, cases)
                results.append((accuracy, params))
                print(f"Trial: C={c:3} | W={w:3} | P={p:3} | Accuracy: {accuracy:6.1f}%")

    # Sort and show Top 3
    results.sort(key=lambda x: x[0], reverse=True)
    
    print("\n" + "=" * 50)
    print("🏆 CALIBRATION WINNERS (Top 3):")
    for acc, p in results[:3]:
        print(f"  Accuracy: {acc:.1f}% | Params: {p}")
    print("=" * 50)

    # Save to report
    report_path = REPO_ROOT / "docs/reports/SH-VAL-001-grid-search.json"
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Full grid search report saved to: {report_path}")

if __name__ == "__main__":
    main()
