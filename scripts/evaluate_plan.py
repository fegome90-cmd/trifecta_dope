#!/usr/bin/env python3
"""Evaluation script for ctx.plan vs ctx.search.

Usage:
    python3 scripts/evaluate_plan.py --segment /path/to/segment
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


# 20 evaluation tasks
TASKS = [
    # Meta tasks (10)
    "how does the context pack build process work?",
    "what is the architecture of the telemetry system?",
    "where are the CLI commands defined?",
    "plan the implementation of token tracking",
    "guide me through the search use case",
    "overview of the clean architecture layers",
    "explain the telemetry event flow",
    "design a new ctx.stats command",
    "status of the context pack validation",
    "description of the prime structure",
    # Impl tasks (10)
    "implement the stats use case function",
    "find the SearchUseCase class",
    "code for telemetry.event() method",
    "symbols in cli.py for ctx commands",
    "files in src/application/ directory",
    "function _estimate_tokens implementation",
    "class Telemetry initialization",
    "import statements in telemetry_reports.py",
    "method flush() implementation details",
    "code pattern for use case execute",
]


def run_search(segment: Path, task: str) -> dict:
    """Run ctx.search and return result."""
    cmd = [
        "uv",
        "run",
        "trifecta",
        "ctx",
        "search",
        "-s",
        str(segment),
        "--query",
        task,
        "--limit",
        "5",
    ]
    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=segment.parent.parent
    )
    output = result.stdout

    # Parse output for hits
    has_results = "No results found" not in output and len(output.strip()) > 0
    hit_count = output.count("chunk:") if has_results else 0

    return {"task": task, "hit": has_results, "hit_count": hit_count, "output": output}


def run_plan(segment: Path, task: str) -> dict:
    """Run ctx.plan and return result."""
    cmd = [
        "uv",
        "run",
        "trifecta",
        "ctx",
        "plan",
        "-s",
        str(segment),
        "--task",
        task,
        "--json",
    ]
    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=segment.parent.parent
    )
    output = result.stdout

    try:
        plan_data = json.loads(output)
        return {
            "task": task,
            "plan_hit": plan_data.get("plan_hit", False),
            "selected_feature": plan_data.get("selected_feature"),
            "chunk_ids": plan_data.get("chunk_ids", []),
            "paths": plan_data.get("paths", []),
            "output": output,
        }
    except json.JSONDecodeError:
        return {"task": task, "plan_hit": False, "error": "Failed to parse", "output": output}


def main():
    parser = argparse.ArgumentParser(description="Evaluate ctx.plan vs ctx.search")
    parser.add_argument("--segment", "-s", type=Path, default=Path("."), help="Segment path")
    parser.add_argument("--baseline", action="store_true", help="Run baseline with ctx.search")
    parser.add_argument("--evaluate", action="store_true", help="Run evaluation with ctx.plan")
    args = parser.parse_args()

    segment = args.segment

    if args.baseline:
        print("=" * 60)
        print("BASELINE: ctx.search")
        print("=" * 60)
        print()

        results = []
        hits = 0
        zero_hits = 0

        for i, task in enumerate(TASKS, 1):
            print(f"[{i}/20] {task[:50]}...")
            result = run_search(segment, task)
            results.append(result)

            if result["hit"]:
                hits += 1
                print(f"        → HIT ({result['hit_count']} chunks)")
            else:
                zero_hits += 1
                print("        → ZERO HIT")

        print()
        print("=" * 60)
        print("BASELINE RESULTS")
        print("=" * 60)
        print(f"Total tasks: {len(TASKS)}")
        print(f"Hits: {hits} ({hits/len(TASKS)*100:.1f}%)")
        print(f"Zero-hits: {zero_hits} ({zero_hits/len(TASKS)*100:.1f}%)")
        print()

    elif args.evaluate:
        print("=" * 60)
        print("EVALUATION: ctx.plan")
        print("=" * 60)
        print()

        results = []
        plan_hits = 0
        plan_misses = 0

        for i, task in enumerate(TASKS, 1):
            print(f"[{i}/20] {task[:50]}...")
            result = run_plan(segment, task)
            results.append(result)

            if result["plan_hit"]:
                plan_hits += 1
                print(f"        → PLAN HIT: {result['selected_feature']}")
            else:
                plan_misses += 1
                print("        → NO PLAN HIT")

        print()
        print("=" * 60)
        print("PLAN EVALUATION RESULTS")
        print("=" * 60)
        print(f"Total tasks: {len(TASKS)}")
        print(f"Plan hits: {plan_hits} ({plan_hits/len(TASKS)*100:.1f}%)")
        print(f"Plan misses: {plan_misses} ({plan_misses/len(TASKS)*100:.1f}%)")
        print()

    else:
        print("Error: Must specify --baseline or --evaluate")
        sys.exit(1)


if __name__ == "__main__":
    main()
