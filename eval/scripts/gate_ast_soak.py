import argparse
import json
import logging
import sys
from pathlib import Path


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )


def main():
    parser = argparse.ArgumentParser(description="Deterministic Gate for AST Soak Run")
    parser.add_argument("--in", dest="input_file", required=True, help="Input Metrics JSON")
    parser.add_argument("--min-ops", type=int, default=1, help="Minimum ops completed")
    parser.add_argument("--max-timeouts", type=int, default=0, help="Max lock timeouts allowed")
    args = parser.parse_args()

    input_path = Path(args.input_file)
    if not input_path.exists():
        logging.error(f"Metrics file not found: {input_path}")
        sys.exit(1)

    with open(input_path, "r") as f:
        metrics = json.load(f)

    # 1. Ops Completed Gate
    ops = metrics.get("ops_completed", 0)
    if ops < args.min_ops:
        logging.error(f"FAIL: Ops completed ({ops}) < Min required ({args.min_ops})")
        sys.exit(1)
    logging.info(f"PASS: Ops completed ({ops}) >= {args.min_ops}")

    # 2. Lock Timeouts Gate (Strict)
    timeouts = metrics.get("lock_contention", {}).get("timeouts", 0)
    if timeouts > args.max_timeouts:
        logging.error(f"FAIL: Lock timeouts ({timeouts}) > Max allowed ({args.max_timeouts})")
        sys.exit(1)
    logging.info(f"PASS: Lock timeouts ({timeouts}) <= {args.max_timeouts}")

    # 3. Cache Effectiveness Check (Informational)
    # Just to confirm we are actually using cache (hits > 0 or at least valid latency)
    hits = metrics.get("counts", {}).get("ast.cache.hit", 0)
    misses = metrics.get("counts", {}).get("ast.cache.miss", 0)
    logging.info(f"INFO: Cache Stats: Hits={hits}, Misses={misses}")

    logging.info("GATE PASSED: All checks green.")
    sys.exit(0)


if __name__ == "__main__":
    setup_logging()
    main()
