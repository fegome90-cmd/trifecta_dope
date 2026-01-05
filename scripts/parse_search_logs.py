#!/usr/bin/env python3
import json
import re
from pathlib import Path

LOG_DIR = Path("_ctx/logs/search_dataset_v1")
SUMMARY_PATH = Path("_ctx/metrics/search_dataset_v1_summary.json")

def parse_log(path):
    content = path.read_text()
    
    # Extract OUTPUT block
    try:
        # Looking for the marker from runner_impl.py
        output_block = content.split("OUTPUT (STDOUT+STDERR):\n")[1]
    except IndexError:
        output_block = ""
        
    # Count hits: look for lines "X. [id] path"
    # Regex: Start of line, number, dot, space, bracket
    hits = re.findall(r"^\d+\.\s+\[.*?\]\s+. *", output_block, re.MULTILINE)
    
    paths = []
    for h in hits:
        # Extract path after closing bracket
        # "1. [id] path/to/file"
        parts = h.split("] ", 1)
        if len(parts) > 1:
            paths.append(parts[1].strip())
            
    return {
        "hits": len(hits),
        "paths": paths
    }

def main():
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    logs = list(LOG_DIR.glob("*.log"))
    results = []
    
    for log in logs:
        # Filename format: qXX_class.log
        parts = log.stem.split("_")
        if len(parts) < 2:
            continue
            
        qid = parts[0]
        # Handle cases where class might have underscores, though v1 dataset is simple
        qclass = parts[1]
        
        parsed = parse_log(log)
        results.append({
            "id": qid,
            "class": qclass,
            **parsed
        })
        
    # Metrics Calculation
    summary = {"total": len(results), "by_class": {}}
    
    # Ensure all classes exist even if empty
    for cls in ["vague", "semi", "guided"]:
        items = [r for r in results if r["class"] == cls]
        
        if not items:
            summary["by_class"][cls] = {
                "count": 0,
                "hit_rate": 0.0,
                "avg_hits": 0.0,
                "unique_paths_avg": 0.0
            }
            continue
            
        hits_gt_0 = sum(1 for r in items if r["hits"] > 0)
        total_hits = sum(r["hits"] for r in items)
        total_unique = sum(len(set(r["paths"])) for r in items)
        
        summary["by_class"][cls] = {
            "count": len(items),
            "hit_rate": round(hits_gt_0 / len(items), 2),
            "avg_hits": round(total_hits / len(items), 2),
            "unique_paths_avg": round(total_unique / len(items), 2)
        }
        
    with open(SUMMARY_PATH, "w") as f:
        json.dump(summary, f, indent=2)
        
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()