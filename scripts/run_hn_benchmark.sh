#!/usr/bin/env bash
set -euo pipefail

# HN Benchmark Runner
# Compares Baseline Context Dumping vs CLI with PCC

echo "============================================================"
echo "HN Benchmark: Baseline vs CLI with PCC"
echo "============================================================"

# Print configuration
echo "Corpus Revision: $(git rev-parse HEAD)"
echo "Date: $(date -Iseconds)"
echo ""

# Run the benchmark
python scripts/run_hn_benchmark.py

echo ""
echo "Results written to:"
echo "  - data/hn_runs.csv"
echo "  - docs/hn_methodology.md"
echo "  - docs/hn_results.md"
