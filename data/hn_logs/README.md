# HN Benchmark Logs

This directory contains raw logs from the HN benchmark runs.

## Structure

```
data/hn_logs/
├── baseline/   # Logs from baseline (context dump) trials
└── cli/       # Logs from CLI (PCC) trials
```

## Current Status

As of the initial benchmark run, the logs are embedded in the CSV output (`data/hn_runs.csv`).

## How to Read

Each row in `hn_runs.csv` represents one trial:
- `scenario`: "baseline" or "cli"
- `run_id`: Unique identifier (e.g., "baseline_001")
- `pass`: Whether the trial passed
- `tokens_in`: Tokens sent to the CLI
- `tokens_out`: Tokens returned from the CLI
- `total_tokens`: tokens_in + tokens_out
- `cost_est`: Estimated cost
- `wall_time_s`: Wall time in seconds
- `tool_calls`: Number of CLI tool calls
- `avg_tool_rtt_ms`: Average tool round-trip time in ms
- `p95_tool_rtt_ms`: 95th percentile RTT in ms
- `zero_hit_rate`: Percentage of searches with 0 hits
- `corpus_rev`: Git commit SHA
- `tau`: Relevance threshold
- `model`: Model used
- `temperature`: Temperature setting
- `timestamp`: ISO timestamp
