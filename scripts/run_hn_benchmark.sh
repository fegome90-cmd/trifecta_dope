#!/usr/bin/env bash
set -e

# Setup
export CORPUS_REV=$(git rev-parse HEAD)
export TRIFECTA_TELEMETRY_LEVEL="off" # Disable telemetry to avoid noise during benchmark? Or keep it? The prompt says "Capture ... telemetry logs".
# Wait, prompt: "Store per-run raw logs in data/hn_logs/<scenario>/<run_id>/".
# The Python script writes to CSV.
# The raw logs (stdout/stderr) should be captured by the wrapper script or the python script.

# Let's adjust the wrapper to capture stdout/stderr of the python runner.
# But the python runner runs multiple trials.
# I should probably modify the python runner to log to files or just let the wrapper do it.

# Actually, the python runner prints progress.
# I will make the python runner invoke the CLI commands and capture their output internally for token counting, but I also need to save them.

# Re-thinking: The prompt says "Store per-run raw logs".
# My python script captures output in memory. I should write it to files.
# I will modify `scripts/benchmark_runner.py` to write logs.

# But first, let's write the shell script.

mkdir -p data/hn_logs
mkdir -p data

echo "Starting HN Benchmark"
echo "Corpus Revision: $CORPUS_REV"
echo "Date: $(date)"

# Run Baseline
echo "Running Scenario A: Baseline (N=10)..."
python3 scripts/benchmark_runner.py --scenario A --trials 10 --output data/hn_runs.csv

# Run CLI
echo "Running Scenario B: CLI (N=10)..."
python3 scripts/benchmark_runner.py --scenario B --trials 10 --output data/hn_runs.csv

echo "Benchmark Complete. Results in data/hn_runs.csv"
