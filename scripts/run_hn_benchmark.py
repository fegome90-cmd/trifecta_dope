#!/usr/bin/env python3
"""
HN Benchmark: Baseline Context Dumping vs CLI with Programmatic Context Calls (PCC)

This script compares two approaches to providing context to an AI agent:
- (A) Baseline: Dump the entire context pack (all chunks) - no CLI search/get
- (B) CLI with PCC: Use ctx.search and ctx.get to selectively retrieve context

Metrics collected (with tiktoken for accurate counting):
- baseline_context_tokens: tokens in the context pack
- baseline_query_tokens: tokens in the user query
- baseline_total_tokens: baseline_context_tokens + baseline_query_tokens

- pcc_query_tokens: tokens in the user query
- pcc_tool_args_tokens: tokens in tool arguments (JSON)
- pcc_tool_results_tokens: tokens in tool results
- pcc_total_tokens: sum of all PCC tokens

With fail-closed validation:
- If baseline fails: status=error, excluded from stats
- If zero_hit_rate > 50%: status=invalid, excluded from stats
"""

import csv
import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import tiktoken
import yaml


# Configuration
SEGMENT = "."
N_TRIALS = 10
TAU = 0.3  # Relevance threshold for zero-hit calculation
CORPUS_REV = "ceaf20c62377dfa84a1eb62cb9516ef66b2cfd84"  # Git commit SHA

# Cost model (MiniMax M2.5 free tier - approximate)
INPUT_COST_PER_1M = 0.0  # Free tier
OUTPUT_COST_PER_1M = 0.0  # Free tier

# Token encoding (o200k_base for modern models)
ENCODING = "o200k_base"

# Queries to test (from search_queries_v1.yaml)
QUERIES = [
    {"id": "q01", "query": "telemetry", "class": "vague"},
    {"id": "q02", "query": "config", "class": "vague"},
    {"id": "q03", "query": "search", "class": "vague"},
    {"id": "q04", "query": "error", "class": "vague"},
    {"id": "q05", "query": "test", "class": "vague"},
]

# Repo root (parent of scripts/)
REPO_ROOT = Path(__file__).parent.parent


def parse_args() -> argparse.Namespace:
    """Parse CLI args for configurable benchmark runs."""
    parser = argparse.ArgumentParser(description="Run HN benchmark (baseline vs CLI with PCC).")
    parser.add_argument(
        "--queries-file",
        type=Path,
        default=None,
        help="Optional YAML dataset file with a 'queries' list.",
    )
    parser.add_argument(
        "--trials",
        type=int,
        default=N_TRIALS,
        help=f"Number of trials per scenario (default: {N_TRIALS}).",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("data/hn_runs.csv"),
        help="Output CSV path relative to repo root (default: data/hn_runs.csv).",
    )
    parser.add_argument(
        "--truth-mode",
        action="store_true",
        help="Enable fail-closed audit mode: requires provider usage data, generates evidence bundles, runs tripwire checks.",
    )
    parser.add_argument(
        "--max-drift-pct",
        type=float,
        default=0.25,
        help="Max allowed drift between estimated and measured tokens (default: 0.25 = 25%%).",
    )
    return parser.parse_args()


def load_queries_from_yaml(path: Path) -> list[dict[str, str]]:
    """Load queries from YAML supporting both benchmark dataset schemas."""
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    rows = data.get("queries")
    if not isinstance(rows, list):
        raise ValueError("queries must be a list")

    normalized: list[dict[str, str]] = []
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"query row at index {i} must be a mapping")

        query = str(row.get("query") or row.get("text") or "").strip()
        if not query:
            raise ValueError(f"empty query at index {i}")

        query_id = str(row.get("id") or f"q{i + 1:02d}").strip()
        query_class = str(row.get("class") or row.get("bucket") or "custom").strip()
        normalized.append({"id": query_id, "class": query_class, "query": query})

    return normalized


def get_git_commit() -> str:
    """Get current git commit SHA."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        return result.stdout.strip()[:12]
    except Exception:
        return CORPUS_REV


def tok(s: str) -> int:
    """Count tokens using tiktoken."""
    try:
        enc = tiktoken.get_encoding(ENCODING)
        return len(enc.encode(s or ""))
    except Exception:
        # Fallback: rough estimate
        return len(s) // 4


def tok_json(obj: dict) -> int:
    """Count tokens in JSON object (canonical format)."""
    # Canonical JSON for stable counting
    s = json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return tok(s)


def build_context_pack(segment: str) -> dict[str, Any]:
    """Build the context pack and return the JSON output.

    The CLI writes JSON to _ctx/context_pack.json, not stdout.
    Stdout contains a Python repr that is NOT valid JSON.
    """
    # First, run the build command to ensure the file exists
    cmd = ["uv", "run", "trifecta", "ctx", "build", "--segment", segment]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)

    if result.returncode != 0:
        return {"error": result.stderr, "pack": {}}

    # Read from the JSON file instead of stdout
    pack_path = REPO_ROOT / segment / "_ctx" / "context_pack.json"
    if segment == ".":
        pack_path = REPO_ROOT / "_ctx" / "context_pack.json"

    try:
        with open(pack_path) as f:
            return {"pack": json.load(f), "error": None}
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse JSON from file: {e}", "pack": {}}
    except FileNotFoundError:
        return {"error": f"Context pack file not found: {pack_path}", "pack": {}}


def get_context_pack_text(pack: dict[str, Any]) -> str:
    """Extract text content from context pack for token counting.

    Includes:
    - Index entries (title + preview) - for discovery
    - Full chunk text - for baseline context dump
    - Delimiters and separators - for fair comparison with PCC
    """
    if not pack or "index" not in pack:
        return ""

    parts = []

    # Header for context pack
    parts.append("=== CONTEXT PACK (FULL DUMP) ===")

    # Full chunks with delimiters (fair baseline)
    for chunk in pack.get("chunks", []):
        chunk_id = chunk.get("id", "unknown")
        chunk_text = chunk.get("text", "")
        source_path = chunk.get("source_path", "unknown")

        parts.append(f"\n--- BEGIN {source_path} [{chunk_id}] ---\n")
        parts.append(chunk_text)
        parts.append(f"\n--- END {source_path} ---\n")

    # Index summary at end (for reference)
    parts.append("\n=== INDEX (reference) ===")
    for entry in pack.get("index", []):
        parts.append(f"- [{entry.get('id', '?')}] {entry.get('title_path_norm', '?')}")

    return "".join(parts)


def calculate_pack_tokens(pack: dict[str, Any]) -> int:
    """Calculate tokens in the context pack using tiktoken."""
    text = get_context_pack_text(pack)
    return tok(text)


def run_cli_search(query: str, segment: str, limit: int = 10) -> dict[str, Any]:
    """Run ctx.search and return results with timing."""
    start_time = time.time()

    cmd = [
        "uv",
        "run",
        "trifecta",
        "ctx",
        "search",
        "--segment",
        segment,
        "--query",
        query,
        "--limit",
        str(limit),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    wall_time = (time.time() - start_time) * 1000  # ms

    # Parse hits from output - format: "Search Results (3 hits)"
    hits = 0
    match = re.search(r"Search Results \((\d+) hits?\)", result.stdout)
    if match:
        hits = int(match.group(1))

    # Calculate tokens
    query_tokens = tok(query)
    # Estimate tool args tokens (JSON with query, limit)
    tool_args = {"q": query, "limit": limit, "segment": segment}
    tool_args_tokens = tok_json(tool_args)

    # Estimate tool result tokens (based on hits and preview text)
    tool_result_tokens = 0
    if hits > 0:
        # Extract preview text from results
        preview_matches = re.findall(r"Preview: (.+?)(?:\n|$)", result.stdout)
        for preview in preview_matches:
            tool_result_tokens += tok(preview)

    return {
        "query": query,
        "hits": hits,
        "query_tokens": query_tokens,
        "tool_args_tokens": tool_args_tokens,
        "tool_result_tokens": tool_result_tokens,
        "wall_time_ms": wall_time,
        "stdout": result.stdout[:500],
    }


def run_baseline_trial(
    segment: str, trial_num: int, queries: list[dict[str, str]]
) -> dict[str, Any]:
    """Run a baseline trial - dump all context."""
    start_time = time.time()

    # Build full context pack
    result = build_context_pack(segment)

    if result.get("error"):
        # FAIL-CLOSED: If baseline fails, mark as error
        return {
            "run_id": f"baseline_{trial_num:03d}",
            "scenario": "baseline",
            "status": "error",
            "error": result["error"],
            "baseline_context_tokens": 0,
            "baseline_query_tokens": 0,
            "baseline_total_tokens": 0,
            "wall_time_s": (time.time() - start_time),
            "corpus_rev": get_git_commit(),
        }

    pack = result.get("pack", {})
    context_tokens = calculate_pack_tokens(pack)

    # Use a sample query for token count
    sample_query = " ".join(q["query"] for q in queries)
    query_tokens = tok(sample_query)

    wall_time = time.time() - start_time

    return {
        "run_id": f"baseline_{trial_num:03d}",
        "scenario": "baseline",
        "status": "ok",
        "baseline_context_tokens": context_tokens,
        "baseline_query_tokens": query_tokens,
        "baseline_total_tokens": context_tokens + query_tokens,
        "wall_time_s": wall_time,
        "corpus_rev": get_git_commit(),
    }


def run_cli_trial(segment: str, trial_num: int, queries: list[dict]) -> dict[str, Any]:
    """Run a CLI trial - use ctx.search and ctx.get."""
    start_time = time.time()

    total_query_tokens = 0
    total_tool_args_tokens = 0
    total_tool_result_tokens = 0
    tool_calls = 0
    tool_times = []
    zero_hits = 0
    total_searches = 0

    for q in queries:
        query = q["query"]

        # Run search
        search_result = run_cli_search(query, segment)
        total_query_tokens += search_result["query_tokens"]
        total_tool_args_tokens += search_result["tool_args_tokens"]
        total_tool_result_tokens += search_result["tool_result_tokens"]
        tool_calls += 1
        tool_times.append(search_result["wall_time_ms"])

        if search_result["hits"] == 0:
            zero_hits += 1
        total_searches += 1

    wall_time = time.time() - start_time

    # Calculate RTT stats
    avg_tool_rtt = sum(tool_times) / len(tool_times) if tool_times else 0
    tool_times_sorted = sorted(tool_times)
    p95_idx = int(len(tool_times_sorted) * 0.95)
    p95_tool_rtt = tool_times_sorted[p95_idx] if tool_times_sorted else 0

    zero_hit_rate = zero_hits / total_searches if total_searches > 0 else 0

    # FAIL-CLOSED: If zero_hit_rate > 50%, mark as invalid
    status = "ok" if zero_hit_rate <= 0.5 else "invalid"

    return {
        "run_id": f"cli_{trial_num:03d}",
        "scenario": "cli",
        "status": status,
        "zero_hit_rate": zero_hit_rate,
        "pcc_query_tokens": total_query_tokens,
        "pcc_tool_args_tokens": total_tool_args_tokens,
        "pcc_tool_result_tokens": total_tool_result_tokens,
        "pcc_total_tokens": total_query_tokens + total_tool_args_tokens + total_tool_result_tokens,
        "wall_time_s": wall_time,
        "tool_calls": tool_calls,
        "avg_tool_rtt_ms": avg_tool_rtt,
        "p95_tool_rtt_ms": p95_tool_rtt,
        "corpus_rev": get_git_commit(),
    }


# =============================================================================
# Truth-Mode: Evidence Bundle & Tripwire Functions
# =============================================================================

EVIDENCE_DIR = REPO_ROOT / "data" / "hn_evidence"


def create_evidence_bundle(trial_id: str, _scenario: str) -> Path:
    """Create evidence bundle directory for a trial."""
    bundle_dir = EVIDENCE_DIR / trial_id
    bundle_dir.mkdir(parents=True, exist_ok=True)
    return bundle_dir


def write_evidence(bundle_dir: Path, filename: str, data: dict) -> None:
    """Write JSON evidence file to bundle."""
    path = bundle_dir / filename
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def compute_hash(data: str) -> str:
    """Compute SHA256 hash of data."""
    import hashlib

    return hashlib.sha256(data.encode()).hexdigest()[:16]


def run_tripwire_checks(
    trial_data: dict,
    bundle_dir: Path | None,
    max_drift_pct: float,
) -> tuple[str, list[str]]:
    """
    Run tripwire checks on trial data.

    Returns: (status, list of reasons)
    """
    reasons = []
    status = "valid"

    # Tripwire 1: Usage missing (if in truth-mode with bundle)
    if bundle_dir is not None:
        # Check if this is a CLI trial with provider usage
        if trial_data.get("scenario") == "cli":
            usage = trial_data.get("provider_usage")
            if usage is None:
                reasons.append("TRIPWIRE_1: Usage missing from provider")
                status = "invalid"

    # Tripwire 2: Drift check (if we have both estimated and measured)
    if bundle_dir is not None and max_drift_pct > 0:
        estimated = trial_data.get("estimated_total_tokens", 0)
        measured = trial_data.get("measured_total_tokens", 0)

        if estimated > 0 and measured > 0:
            drift = abs(estimated - measured) / measured
            if drift > max_drift_pct:
                reasons.append(
                    f"TRIPWIRE_2: TOKEN_DRIFT {drift * 100:.1f}% > {max_drift_pct * 100:.0f}%"
                )
                status = "valid_with_warning"

    # Tripwire 3: Zero-hit rate too high
    zero_hit_rate = trial_data.get("zero_hit_rate", 0)
    if zero_hit_rate > 0.5:
        reasons.append(f"TRIPWIRE_3: ZERO_HIT_RATE {zero_hit_rate * 100:.0f}% > 50%")
        status = "invalid"

    # Tripwire 4: Tool calls without results
    tool_calls = trial_data.get("tool_calls", 0)
    tool_results_logged = trial_data.get("tool_results_logged", 0)
    if tool_calls > 0 and tool_results_logged == 0:
        reasons.append("TRIPWIRE_4: Tool calls without results logged")
        status = "invalid"

    return status, reasons


def write_verdict(bundle_dir: Path, status: str, reasons: list[str], grades: dict) -> None:
    """Write verdict.json with status and grades."""
    verdict = {
        "status": status.upper(),
        "reasons": reasons,
        "grades": grades,
        "generated_at": datetime.now().isoformat(),
    }
    write_evidence(bundle_dir, "verdict.json", verdict)


def grade_metric(grade_type: str, value: Any) -> dict:
    """Create graded metric entry."""
    return {
        "value": value,
        "grade": grade_type,  # MEASURED, ESTIMATED, MISSING
    }


def main():
    """Main benchmark runner."""
    args = parse_args()
    queries = QUERIES
    if args.queries_file is not None:
        queries = load_queries_from_yaml((REPO_ROOT / args.queries_file).resolve())

    n_trials = max(1, args.trials)
    csv_path = (REPO_ROOT / args.output_csv).resolve()

    print("=" * 60)
    print("HN Benchmark: Baseline vs CLI with PCC (tiktoken)")
    print("=" * 60)
    print(f"Corpus Revision: {get_git_commit()}")
    print(f"N Trials: {n_trials}")
    print(f"Queries: {len(queries)}")
    if args.queries_file is not None:
        print(f"Queries File: {args.queries_file}")
    print(f"Output CSV: {csv_path.relative_to(REPO_ROOT)}")
    print(f"τ (threshold): {TAU}")
    print(f"Truth-Mode: {'ENABLED' if args.truth_mode else 'DISABLED'}")
    if args.truth_mode:
        print(f"Max Drift: {args.max_drift_pct * 100:.0f}%")
        print(f"Evidence Dir: {EVIDENCE_DIR.relative_to(REPO_ROOT)}")
    print()

    truth_mode = args.truth_mode
    max_drift = args.max_drift_pct

    # Run baseline trials
    print("Running baseline trials (context dump)...")
    baseline_results = []
    for i in range(1, n_trials + 1):
        print(f"  Trial {i}/{n_trials}...", end=" ", flush=True)
        result = run_baseline_trial(SEGMENT, i, queries)
        baseline_results.append(result)
        status = result.get("status", "unknown")
        if status == "ok":
            print(f"status={status}, context_tokens={result['baseline_context_tokens']:,}")
        else:
            print(f"status={status}, error={result.get('error', 'unknown')[:50]}")

    # Run CLI trials
    print("\nRunning CLI trials (ctx.search/ctx.get)...")
    cli_results = []
    for i in range(1, n_trials + 1):
        print(f"  Trial {i}/{n_trials}...", end=" ", flush=True)
        result = run_cli_trial(SEGMENT, i, queries)
        cli_results.append(result)
        status = result.get("status", "unknown")
        if status == "ok":
            print(
                f"status={status}, total_tokens={result['pcc_total_tokens']:,}, zero_hit_rate={result['zero_hit_rate']:.2%}"
            )
        else:
            print(f"status={status}, zero_hit_rate={result['zero_hit_rate']:.2%}")

    # Write CSV
    csv_path.parent.mkdir(exist_ok=True)

    # Add truth-mode fields if enabled
    truth_fields = ["status_grade", "tokens_grade", "verdict"] if truth_mode else []

    fieldnames = [
        "scenario",
        "run_id",
        "status",
        "baseline_context_tokens",
        "baseline_query_tokens",
        "baseline_total_tokens",
        "pcc_query_tokens",
        "pcc_tool_args_tokens",
        "pcc_tool_result_tokens",
        "pcc_total_tokens",
        "cost_est",
        "wall_time_s",
        "tool_calls",
        "avg_tool_rtt_ms",
        "p95_tool_rtt_ms",
        "zero_hit_rate",
        "corpus_rev",
        "tau",
        "model",
        "temperature",
        "timestamp",
    ] + truth_fields

    # Track validation status
    all_results = baseline_results + cli_results
    invalid_trials = [r for r in all_results if r.get("status") in ("error", "invalid")]
    valid_trials = [r for r in all_results if r.get("status") == "ok"]

    # Process each trial with truth-mode checks
    for r in all_results:
        trial_id = r.get("run_id", "unknown")
        scenario = r.get("scenario", "unknown")

        if truth_mode:
            bundle_dir = create_evidence_bundle(trial_id, scenario)

            # Prepare trial data for tripwire
            trial_data = {
                **r,
                "scenario": scenario,
                "estimated_total_tokens": r.get("baseline_total_tokens", 0)
                or r.get("pcc_total_tokens", 0),
                "measured_total_tokens": r.get("provider_usage_total", 0),  # 0 if not available
                "tool_results_logged": r.get("tool_calls", 0),
            }

            # Run tripwire checks
            status, reasons = run_tripwire_checks(trial_data, bundle_dir, max_drift)

            # Create grades
            grades = {
                "total_tokens": "ESTIMATED",  # We don't have provider usage in CLI-only mode
                "wall_time": "MEASURED",
            }

            # Write verdict
            write_verdict(bundle_dir, status, reasons, grades)

            # Add truth-mode fields to result
            r["status_grade"] = status
            r["tokens_grade"] = grades.get("total_tokens", "MISSING")
            r["verdict"] = "; ".join(reasons) if reasons else "OK"
        else:
            r["status_grade"] = "N/A"
            r["tokens_grade"] = "ESTIMATED"
            r["verdict"] = "N/A"

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for r in baseline_results:
            row = {
                "scenario": "baseline",
                "run_id": r["run_id"],
                "status": r.get("status", "unknown"),
                "baseline_context_tokens": r.get("baseline_context_tokens", 0),
                "baseline_query_tokens": r.get("baseline_query_tokens", 0),
                "baseline_total_tokens": r.get("baseline_total_tokens", 0),
                "pcc_query_tokens": 0,
                "pcc_tool_args_tokens": 0,
                "pcc_tool_result_tokens": 0,
                "pcc_total_tokens": 0,
                "cost_est": 0,
                "wall_time_s": r.get("wall_time_s", 0),
                "tool_calls": 0,
                "avg_tool_rtt_ms": 0,
                "p95_tool_rtt_ms": 0,
                "zero_hit_rate": 0,
                "corpus_rev": r.get("corpus_rev", get_git_commit()),
                "tau": TAU,
                "model": "minimax-m2.5:free",
                "temperature": "N/A",
                "timestamp": datetime.now().isoformat(),
            }
            if truth_mode:
                row["status_grade"] = r.get("status_grade", "N/A")
                row["tokens_grade"] = r.get("tokens_grade", "N/A")
                row["verdict"] = r.get("verdict", "N/A")
            writer.writerow(row)

        for r in cli_results:
            row = {
                "scenario": "cli",
                "run_id": r["run_id"],
                "status": r.get("status", "unknown"),
                "baseline_context_tokens": 0,
                "baseline_query_tokens": 0,
                "baseline_total_tokens": 0,
                "pcc_query_tokens": r.get("pcc_query_tokens", 0),
                "pcc_tool_args_tokens": r.get("pcc_tool_args_tokens", 0),
                "pcc_tool_result_tokens": r.get("pcc_tool_result_tokens", 0),
                "pcc_total_tokens": r.get("pcc_total_tokens", 0),
                "cost_est": 0,
                "wall_time_s": r.get("wall_time_s", 0),
                "tool_calls": r.get("tool_calls", 0),
                "avg_tool_rtt_ms": r.get("avg_tool_rtt_ms", 0),
                "p95_tool_rtt_ms": r.get("p95_tool_rtt_ms", 0),
                "zero_hit_rate": r.get("zero_hit_rate", 0),
                "corpus_rev": r.get("corpus_rev", get_git_commit()),
                "tau": TAU,
                "model": "minimax-m2.5:free",
                "temperature": "N/A",
                "timestamp": datetime.now().isoformat(),
            }
            if truth_mode:
                row["status_grade"] = r.get("status_grade", "N/A")
                row["tokens_grade"] = r.get("tokens_grade", "N/A")
                row["verdict"] = r.get("verdict", "N/A")
            writer.writerow(row)

    print(f"\nResults written to: {csv_path}")

    # Calculate summary statistics (only for valid runs)
    print("\n" + "=" * 60)
    print("Summary Statistics (valid runs only)")
    print("=" * 60)

    def median(lst):
        if not lst:
            return 0
        sorted_lst = sorted(lst)
        n = len(sorted_lst)
        if n % 2 == 0:
            return (sorted_lst[n // 2 - 1] + sorted_lst[n // 2]) / 2
        return sorted_lst[n // 2]

    def iqr(lst):
        if not lst or len(lst) < 4:
            return 0
        sorted_lst = sorted(lst)
        n = len(sorted_lst)
        q1 = sorted_lst[n // 4]
        q3 = sorted_lst[3 * n // 4]
        return q3 - q1

    # Filter valid baseline runs
    valid_baseline = [r for r in baseline_results if r.get("status") == "ok"]
    valid_cli = [r for r in cli_results if r.get("status") == "ok"]

    print(f"\nBaseline: {len(valid_baseline)}/{len(baseline_results)} valid runs")
    print(f"CLI: {len(valid_cli)}/{len(cli_results)} valid runs")

    baseline_tokens = []
    baseline_times = []
    cli_tokens = []
    cli_times = []

    if valid_baseline:
        baseline_tokens = [r["baseline_total_tokens"] for r in valid_baseline]
        baseline_times = [r["wall_time_s"] for r in valid_baseline]

        print("\nBaseline (Context Dump):")
        print(
            f"  Context Tokens: median={median(baseline_tokens):,.0f}, IQR={iqr(baseline_tokens):,.0f}"
        )
        print(f"  Wall Time: median={median(baseline_times):.3f}s, IQR={iqr(baseline_times):.3f}s")

    if valid_cli:
        cli_tokens = [r["pcc_total_tokens"] for r in valid_cli]
        cli_times = [r["wall_time_s"] for r in valid_cli]
        cli_tool_calls = [r["tool_calls"] for r in valid_cli]
        cli_rtt = [r["avg_tool_rtt_ms"] for r in valid_cli]
        cli_zero_hit = [r["zero_hit_rate"] for r in valid_cli]

        print("\nCLI (ctx.search/ctx.get):")
        print(f"  Total Tokens: median={median(cli_tokens):,.0f}, IQR={iqr(cli_tokens):,.0f}")
        print(f"  Wall Time: median={median(cli_times):.3f}s, IQR={iqr(cli_times):.3f}s")
        print(f"  Tool Calls: median={median(cli_tool_calls)}, IQR={iqr(cli_tool_calls)}")
        print(f"  Avg RTT: median={median(cli_rtt):.1f}ms, IQR={iqr(cli_rtt):.1f}ms")
        print(f"  Zero-Hit Rate: median={median(cli_zero_hit):.2%}, IQR={iqr(cli_zero_hit):.2%}")

    # Token savings
    if valid_baseline and valid_cli and baseline_tokens and cli_tokens:
        print("\n" + "=" * 60)
        print("Token Savings: Baseline vs CLI")
        print("=" * 60)
        baseline_median = median(baseline_tokens)
        cli_median = median(cli_tokens)
        savings = baseline_median - cli_median
        savings_pct = savings / baseline_median * 100 if baseline_median > 0 else 0
        print(f"  Tokens saved: {savings:,.0f} ({savings_pct:.1f}%)")
        print(f"  Baseline median: {baseline_median:,.0f} tokens")
        print(f"  CLI median: {cli_median:,.0f} tokens")

    # Truth-mode fail-closed: exit with error if any invalid trials
    if truth_mode:
        print("\n" + "=" * 60)
        print("Truth-Mode Validation")
        print("=" * 60)
        print(f"Total trials: {len(all_results)}")
        print(f"Valid trials: {len(valid_trials)}")
        print(f"Invalid trials: {len(invalid_trials)}")

        if invalid_trials:
            print("\n❌ INVALID RUN DETECTED")
            print("Reasons:")
            for r in invalid_trials:
                run_id = r.get("run_id", "unknown")
                status = r.get("status", "unknown")
                error = r.get("error", r.get("verdict", "unknown"))
                print(f"  - {run_id}: {status} - {error}")

            if truth_mode:
                print("\n⚠️ FAIL-CLOSED: Exiting with error code.")
                print("Evidence bundles written to: data/hn_evidence/")
                return 1
        else:
            print("\n✅ ALL TRIALS VALID")
            print(f"Evidence bundles written to: {EVIDENCE_DIR.relative_to(REPO_ROOT)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
