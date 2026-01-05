#!/usr/bin/env python3
"""
Search Guidance Baseline Evaluator.
Executes queries from a YAML dataset using `trifecta ctx search` and computes metrics.
"""

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import yaml

# Constants
DATASET_PATH = Path("docs/datasets/search_queries_v1.yaml")
METRICS_DIR = Path("_ctx/metrics")
LOGS_DIR = Path("/tmp/tf_search_logs")
SUMMARY_PATH = METRICS_DIR / "search_dataset_summary.json"


def run_command(cmd: List[str]) -> str:
    """Run a shell command and return stdout."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip()


def parse_search_output(output: str) -> Dict[str, Any]:
    """Parse the text output of `trifecta ctx search`."""
    hits = []
    lines = output.splitlines()
    
    current_hit = {}
    
    # Simple parser for the current CLI output format:
    # 1. [id] path
    #    Score: ...
    #    Preview: ...
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Hit Header: "1. [id] path"
        if line[0].isdigit() and ". [" in line and "]" in line:
            if current_hit:
                hits.append(current_hit)
            
            parts = line.split(". [", 1)
            if len(parts) > 1:
                id_part = parts[1].split("] ", 1)
                chunk_id = id_part[0]
                path = id_part[1] if len(id_part) > 1 else "unknown"
                current_hit = {"id": chunk_id, "path": path, "preview": ""}
        
        # Preview: "Preview: ..."
        elif line.startswith("Preview:"):
            if current_hit:
                current_hit["preview"] = line.replace("Preview:", "").strip()
    
    if current_hit:
        hits.append(current_hit)
        
    return {"hits": hits, "count": len(hits)}


def evaluate_query(query_data: Dict[str, Any], index: int) -> Dict[str, Any]:
    """Run a single query and return metrics."""
    query_text = query_data["text"]
    query_type = query_data["type"]
    anchors = [a.lower() for a in query_data.get("anchors", [])]
    
    # Setup log file
    log_file = LOGS_DIR / f"q{index:02d}_{query_type}.log"
    
    # Run CLI
    start_time = time.time()
    cmd = ["uv", "run", "trifecta", "ctx", "search", "-s", ".", "-q", query_text, "--limit", "5"]
    
    # Capture raw output to log
    result = subprocess.run(cmd, capture_output=True, text=True)
    duration_ms = int((time.time() - start_time) * 1000)
    
    with open(log_file, "w") as f:
        f.write(f"CMD: {' '.join(cmd)}\n")
        f.write("-" * 40 + "\n")
        f.write(f"STDOUT:\n{result.stdout}\n")
        f.write("-" * 40 + "\n")
        f.write(f"STDERR:\n{result.stderr}\n")
    
    # Parse output
    parsed = parse_search_output(result.stdout)
    hits = parsed["hits"]
    hit_count = parsed["count"]
    
    # Metrics
    hit_rate = 1 if hit_count > 0 else 0
    
    # Top K Diversity (unique paths)
    unique_paths = set(h["path"] for h in hits)
    diversity = len(unique_paths)
    
    # Anchor Presence
    anchor_found = False
    if anchors and hit_count > 0:
        # Check if ANY anchor is in ANY hit preview or path
        for hit in hits:
            text_to_search = (hit["path"] + " " + hit["preview"]).lower()
            if any(anchor in text_to_search for anchor in anchors):
                anchor_found = True
                break
    elif not anchors:
        anchor_found = None # N/A for queries without anchors
        
    return {
        "text": query_text,
        "type": query_type,
        "hit_count": hit_count,
        "hit_rate": hit_rate,
        "diversity": diversity,
        "anchor_presence": anchor_found,
        "duration_ms": duration_ms,
        "log_file": str(log_file)
    }


def main():
    # Setup directories
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"Loading dataset from {DATASET_PATH}...")
    with open(DATASET_PATH, "r") as f:
        data = yaml.safe_load(f)
        queries = data["queries"]
    
    print(f"Executing {len(queries)} queries...")
    results = []
    
    for i, q in enumerate(queries, 1):
        print(f"[{i}/{len(queries)}] {q['type'].upper()}: {q['text']}")
        metrics = evaluate_query(q, i)
        results.append(metrics)
    
    # Aggregate Metrics
    by_type = {"vaga": [], "semi": [], "guiada": []}
    for r in results:
        by_type[r["type"]].append(r)
        
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_queries": len(results),
        "overall": {
            "hit_rate": sum(r["hit_rate"] for r in results) / len(results),
            "zero_hits": sum(1 for r in results if r["hit_count"] == 0)
        },
        "by_type": {}
    }
    
    for qtype, items in by_type.items():
        if not items:
            continue
        
        hit_rate = sum(r["hit_rate"] for r in items) / len(items)
        zero_hits = sum(1 for r in items if r["hit_count"] == 0)
        avg_diversity = sum(r["diversity"] for r in items) / len(items)
        
        # Anchor presence (exclude N/A)
        anchored_items = [r for r in items if r["anchor_presence"] is not None]
        anchor_rate = (sum(1 for r in anchored_items if r["anchor_presence"]) / len(anchored_items)) if anchored_items else 0
        
        summary["by_type"][qtype] = {
            "count": len(items),
            "hit_rate": round(hit_rate, 2),
            "zero_hits": zero_hits,
            "zero_hit_pct": round((zero_hits / len(items)) * 100, 1),
            "avg_top_k_diversity": round(avg_diversity, 2),
            "anchor_presence_rate": round(anchor_rate, 2)
        }
    
    # Save Summary
    with open(SUMMARY_PATH, "w") as f:
        json.dump(summary, f, indent=2)
        
    print(f"\n✅ Summary saved to {SUMMARY_PATH}")
    print(json.dumps(summary["by_type"], indent=2))


if __name__ == "__main__":
    main()
