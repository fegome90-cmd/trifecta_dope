import argparse
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path
from statistics import quantiles


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )


def calculate_percentiles(values):
    if not values:
        return {"p50": 0, "p95": 0, "max": 0}
    vals = sorted(values)
    n = len(vals)
    return {
        "p50": vals[int(n * 0.5)],
        "p95": vals[int(n * 0.95)],
        "max": vals[-1],
    }


def main():
    parser = argparse.ArgumentParser(description="Extract AST Soak Metrics from Telemetry")
    parser.add_argument("--run-id", required=True, help="Run ID to filter events")
    parser.add_argument("--out", required=True, help="Output JSON path")
    parser.add_argument(
        "--telemetry-file", default="_ctx/telemetry/events.jsonl", help="Path to events.jsonl"
    )
    args = parser.parse_args()

    telemetry_path = Path(args.telemetry_file)
    if not telemetry_path.exists():
        logging.error(f"Telemetry file not found: {telemetry_path}")
        sys.exit(1)

    logging.info(f"Scanning {telemetry_path} for run_id={args.run_id}...")

    metrics = {
        "run_id": args.run_id,
        "counts": defaultdict(int),
        "latencies": defaultdict(list),
        "ops_completed": 0,  # Successful ast.symbols calls
        "lock_contention": {"timeouts": 0, "waits": 0, "wait_ms_total": 0},
    }

    events_processed = 0
    matched_events = 0

    with open(telemetry_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            events_processed += 1
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            if event.get("run_id") != args.run_id:
                continue

            matched_events += 1
            cmd = event.get("cmd")
            timing = event.get("timing_ms", 0)

            # 1. Basic Counts
            metrics["counts"][cmd] += 1
            metrics["latencies"][cmd].append(timing)

            # 2. Ops Completed (High Level)
            if cmd == "ast.symbols":
                # Check status in result/args??
                # CLI logs result={"status": "ok"}
                res = event.get("result", {})
                if res.get("status") == "ok":
                    metrics["ops_completed"] += 1

            # 3. Lock Logic
            if cmd == "ast.cache.lock_timeout":
                metrics["lock_contention"]["timeouts"] += 1
            elif cmd == "ast.cache.lock_wait":
                metrics["lock_contention"]["waits"] += 1
                metrics["lock_contention"]["wait_ms_total"] += timing

    logging.info(f"Processed {events_processed} lines, matched {matched_events} events.")

    if matched_events == 0:
        logging.warning(f"No events found for run_id={args.run_id}!")

    # Post-process latencies
    final_latencies = {}
    for cmd, vals in metrics["latencies"].items():
        final_latencies[cmd] = calculate_percentiles(vals)

    metrics["latency_ms"] = final_latencies
    del metrics["latencies"]  # Remove raw lists

    # Write output
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w") as f:
        json.dump(metrics, f, indent=2)

    logging.info(f"Metrics written to {out_path}")
    print(json.dumps(metrics, indent=2))  # Print to stdout for piping/debug


if __name__ == "__main__":
    setup_logging()
    main()
