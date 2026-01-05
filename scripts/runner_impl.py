#!/usr/bin/env python3
import yaml
import subprocess
import sys
from pathlib import Path
import time
import shutil

DATASET = Path("docs/datasets/search_queries_v1.yaml")
LOG_DIR = Path("_ctx/logs/search_dataset_v1")

def main():
    if len(sys.argv) > 1:
        dataset_path = Path(sys.argv[1])
    else:
        dataset_path = DATASET
        
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    with open(dataset_path) as f:
        data = yaml.safe_load(f)
    
    queries = data["queries"]
    print(f"Executing {len(queries)} queries from {dataset_path}...")

    for q in queries:
        qid = q["id"]
        qclass = q["class"]
        query = q["query"]
        
        log_path = LOG_DIR / f"{qid}_{qclass}.log"
        
        # Construct exact command string
        # Using list for subprocess but string for log to be copy-pasteable
        cmd_list = ["uv", "run", "trifecta", "ctx", "search", "--segment", ".", "--query", query, "--limit", "6"]
        cmd_str = f"uv run trifecta ctx search --segment . --query \"{query}\" --limit 6"
        
        print(f"CMD: {cmd_str}")
        
        start = time.time()
        # Capture all output (stdout + stderr)
        res = subprocess.run(cmd_list, capture_output=True, text=True)
        duration = time.time() - start
        
        with open(log_path, "w") as f:
            # Header requirement: CMD line first
            f.write(f"CMD: {cmd_str}\n")
            f.write(f"EXIT: {res.returncode}\n")
            f.write(f"DURATION: {duration:.4f}s\n")
            f.write("-" * 40 + "\n")
            f.write("OUTPUT (STDOUT+STDERR):\n")
            f.write(res.stdout)
            f.write(res.stderr)
        
        print(f"[{qid}] Log saved to {log_path}")

if __name__ == "__main__":
    main()
