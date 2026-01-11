#!/usr/bin/env python3
"""
Field Exercises v2 - Hard Query A/B Runner

Deterministic A/B evaluation:
- OFF mode: --no-lint
- ON mode: TRIFECTA_LINT=1
- Telemetry capture per query_hash
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


def load_dataset(dataset_path: Path) -> list[dict[str, Any]]:
    """Load v2 dataset."""
    with open(dataset_path) as f:
        data = yaml.safe_load(f)
    return data["queries"]


def run_query_ab(query_text: str, segment: Path, mode: str) -> dict[str, Any]:
    """Execute single query in OFF or ON mode."""
    env = os.environ.copy()
    env["TRIFECTA_TELEMETRY_DIR"] = str(segment / "_ctx" / "telemetry")

    cmd = [
        "uv",
        "run",
        "trifecta",
        "ctx",
        "search",
        "--segment",
        str(segment),
        "--query",
        query_text,
        "--limit",
        "10",
    ]

    if mode == "off":
        cmd.append("--no-lint")
        env["TRIFECTA_LINT"] = "0"
    elif mode == "on":
        env["TRIFECTA_LINT"] = "1"

    result = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=segment.parent)

    # Parse hits from stdout
    import re

    hits = 0
    match = re.search(r"Search Results \((\d+) hits?\)", result.stdout)
    if match:
        hits = int(match.group(1))

    return {
        "mode": mode,
        "hits": hits,
        "returncode": result.returncode,
        "stdout_preview": result.stdout[:200] if result.stdout else "",
    }


def extract_telemetry_for_query(telemetry_path: Path, query_text: str, mode: str) -> dict[str, Any]:
    """Extract telemetry event for specific query."""
    events = []
    with open(telemetry_path) as f:
        for line in f:
            if not line.strip():
                continue
            try:
                event = json.loads(line)
                if event.get("cmd") == "ctx.search":
                    args = event.get("args", {})
                    if args.get("query_preview") == query_text[:50]:  # Match by preview
                        events.append(event)
            except json.JSONDecodeError:
                continue

    # Return most recent match
    if not events:
        return {}

    event = events[-1]
    args = event.get("args", {})
    result = event.get("result", {})

    return {
        "query_hash": args.get("query_hash"),
        "linter_query_class": args.get("linter_query_class"),
        "linter_expanded": args.get("linter_expanded"),
        "linter_added_strong_count": args.get("linter_added_strong_count", 0),
        "linter_added_weak_count": args.get("linter_added_weak_count", 0),
        "hits": result.get("hits", 0),
    }


def main() -> int:
    """Main A/B runner."""
    repo_root = Path(__file__).resolve().parents[3]
    dataset_path = repo_root / "docs" / "datasets" / "field_exercises_v2.yaml"
    telemetry_path = repo_root / "_ctx" / "telemetry" / "events.jsonl"
    output_path = repo_root / "_ctx" / "metrics" / "field_exercises_v2_ab.json"
    segment = repo_root

    print("📋 Loading dataset...")
    queries = load_dataset(dataset_path)
    print(f"   Loaded {len(queries)} queries")

    results = []

    for i, query in enumerate(queries, 1):
        qid = query["id"]
        bucket = query["bucket"]
        text = query["text"]

        print(f"\n[{i}/{len(queries)}] {qid} ({bucket}): {text[:50]}...")

        # Run OFF mode
        print("   Running OFF mode...")
        off_result = run_query_ab(text, segment, "off")

        # Run ON mode
        print("   Running ON mode...")
        on_result = run_query_ab(text, segment, "on")

        # Extract telemetry for ON mode
        telemetry_on = extract_telemetry_for_query(telemetry_path, text, "on")

        results.append(
            {
                "id": qid,
                "bucket": bucket,
                "query": text,
                "off": {
                    "hits": off_result["hits"],
                    "returncode": off_result["returncode"],
                },
                "on": {
                    "hits": on_result["hits"],
                    "returncode": on_result["returncode"],
                    "telemetry": telemetry_on,
                },
            }
        )

        print(f"   ✅ OFF: {off_result['hits']} hits | ON: {on_result['hits']} hits")

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ Results written to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
