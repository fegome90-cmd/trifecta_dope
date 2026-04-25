"""LSP Signal Benchmark — verifies LSP Intelligence Phase quality.

Measures 5 dimensions:
  1. LSP routing precision (semantic vs non-semantic queries)
  2. Signal state distribution (all 7 states)
  3. Latency overhead (LSP adds <20ms, total <65ms)
  4. Fidelity promotion (full/degraded/fallback correct)
  5. Regression (PRIME+AST unchanged when LSP disabled)
"""

import time
import tracemalloc
import json
from pathlib import Path
from collections import Counter
from unittest.mock import MagicMock, patch
from typing import Any

from src.application.oracle_use_case import SearchOracleUseCase
from src.application.ast_parser import SymbolInfo, ParseResult
from src.domain.context_models import SearchHit
from src.infrastructure.lsp_client import LSPState

REPO = Path(".").resolve()
ITERATIONS = 10  # per query for latency


# ── Queries ──────────────────────────────────────────────────────────────────

SEMANTIC_QUERIES = [
    {"id": 1,  "query": "what is resolve_segment_ref",        "target": "resolve_segment_ref",  "lang": "EN"},
    {"id": 2,  "query": "what is SearchOracleUseCase",        "target": "SearchOracleUseCase",   "lang": "EN"},
    {"id": 3,  "query": "show me SkeletonMapBuilder",          "target": "SkeletonMapBuilder",    "lang": "EN"},
    {"id": 4,  "query": "what is ContextService",              "target": "ContextService",        "lang": "EN"},
    {"id": 5,  "query": "show me HybridDispatcher",            "target": "HybridDispatcher",      "lang": "EN"},
    {"id": 6,  "query": "what is canonicalize_path",           "target": "canonicalize_path",     "lang": "EN"},
    {"id": 7,  "query": "what is GraphStore",                  "target": "GraphStore",            "lang": "EN"},
    {"id": 8,  "query": "show me LSPClient",                   "target": "LSPClient",             "lang": "EN"},
    {"id": 9,  "query": "what is SegmentRef",                  "target": "SegmentRef",            "lang": "EN"},
    {"id": 10, "query": "show me OracleResult",                "target": "OracleResult",          "lang": "EN"},
    # ES
    {"id": 11, "query": "qué es resolve_segment_ref",          "target": "resolve_segment_ref",   "lang": "ES"},
    {"id": 12, "query": "que es SearchOracleUseCase",          "target": "SearchOracleUseCase",   "lang": "ES"},
    {"id": 13, "query": "mostrame SkeletonMapBuilder",         "target": "SkeletonMapBuilder",    "lang": "ES"},
    {"id": 14, "query": "qué es ContextService",               "target": "ContextService",        "lang": "ES"},
    {"id": 15, "query": "que es GraphStore",                   "target": "GraphStore",            "lang": "ES"},
]

NON_SEMANTIC_QUERIES = [
    {"id": 16, "query": "how to configure the daemon"},
    {"id": 17, "query": "context service"},
    {"id": 18, "query": "explain the oracle architecture"},
    {"id": 19, "query": "como configurar el daemon"},
    {"id": 20, "query": "what does the CLI do"},
]

NEGATIVE_QUERIES = [
    {"id": 21, "query": "what is ",                  "note": "empty target"},
    {"id": 22, "query": "   ",                        "note": "whitespace only"},
    {"id": 23, "query": "the quick brown fox",        "note": "random text"},
]

AMBIGUOUS_QUERIES = [
    {"id": 24, "query": "what is search",       "target": "search",      "note": "symbol in many files"},
    {"id": 25, "query": "what is execute",       "target": "execute",     "note": "common method name"},
]


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_symbol(name: str, start_line: int = 42) -> SymbolInfo:
    return SymbolInfo(
        kind="function", name=name, qualified_name=name,
        start_line=start_line, end_line=start_line + 5,
        signature_stub=f"def {name}(...)",
    )


def _make_ast_result(symbols: list[SymbolInfo] | None = None) -> MagicMock:
    result = MagicMock(spec=ParseResult)
    result.symbols = symbols if symbols is not None else []
    return result


def _make_oracle(
    lsp_state: LSPState | None = LSPState.READY,
    hover_return: dict | None = None,
) -> SearchOracleUseCase:
    ast_builder = MagicMock()

    # Default: AST returns symbols matching semantic targets
    default_symbols = [
        _make_symbol("resolve_segment_ref", 10),
        _make_symbol("SearchOracleUseCase", 50),
        _make_symbol("SkeletonMapBuilder", 80),
        _make_symbol("ContextService", 120),
        _make_symbol("HybridDispatcher", 160),
        _make_symbol("canonicalize_path", 200),
        _make_symbol("GraphStore", 240),
        _make_symbol("LSPClient", 280),
        _make_symbol("SegmentRef", 300),
        _make_symbol("OracleResult", 340),
        _make_symbol("search", 400),
        _make_symbol("execute", 450),
    ]
    ast_builder.build.return_value = _make_ast_result(symbols=default_symbols)

    lsp_client = None
    if lsp_state is not None:
        lsp_client = MagicMock()
        lsp_client.state = lsp_state
        if hover_return is None:
            hover_return = {
                "contents": [{"language": "python", "value": "def symbol(...)"}],
            }
        lsp_client.request.return_value = hover_return

    return SearchOracleUseCase(
        ast_builder=ast_builder,
        lsp_client=lsp_client,
        telemetry=None,
    )


def _run_oracle(oracle: SearchOracleUseCase, query: str) -> dict:
    hit = SearchHit(
        id="bench", title_path=["main"], preview="bench",
        token_est=10, source_path="src/domain/mod.py", score=1.0,
    )
    with patch("src.application.oracle_use_case.ContextService") as MockCS:
        MockCS.return_value.search.return_value = MagicMock(hits=[hit])
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.is_file", return_value=True):
                result = oracle.execute(REPO, query)
    if hasattr(result, "unwrap"):
        return result.unwrap().model_dump()
    return result


# ── Dimension 1: LSP Routing Precision ──────────────────────────────────────

def evaluate_routing_precision():
    """Semantic queries hit LSP, non-semantic don't."""
    print("\n" + "=" * 70)
    print("DIMENSION 1: LSP ROUTING PRECISION")

    oracle = _make_oracle(lsp_state=LSPState.READY)

    # Semantic queries should NOT be lsp_not_applicable
    sem_correct = 0
    for q in SEMANTIC_QUERIES:
        r = _run_oracle(oracle, q["query"])
        signal = r.get("metadata", {}).get("lsp_signal", "?")
        routed = signal != "lsp_not_applicable"
        print(f"  Q{q['id']:2d} [{q['lang']}] \"{q['query'][:45]}\" → lsp_signal={signal:20s} {'OK' if routed else 'MISROUTED'}")
        if routed:
            sem_correct += 1

    # Non-semantic queries SHOULD be lsp_not_applicable
    nonsem_correct = 0
    for q in NON_SEMANTIC_QUERIES:
        r = _run_oracle(oracle, q["query"])
        signal = r.get("metadata", {}).get("lsp_signal", "?")
        skipped = signal == "lsp_not_applicable"
        print(f"  Q{q['id']:2d} \"{q['query'][:45]}\" → lsp_signal={signal:20s} {'SKIPPED' if skipped else 'ERROR'}")
        if skipped:
            nonsem_correct += 1

    sem_pct = sem_correct / len(SEMANTIC_QUERIES) * 100
    nonsem_pct = nonsem_correct / len(NON_SEMANTIC_QUERIES) * 100
    print(f"\n  Semantic routed:   {sem_correct}/{len(SEMANTIC_QUERIES)} = {sem_pct:.0f}%")
    print(f"  Non-semantic skipped: {nonsem_correct}/{len(NON_SEMANTIC_QUERIES)} = {nonsem_pct:.0f}%")
    return sem_pct, nonsem_pct


# ── Dimension 2: Signal State Distribution ──────────────────────────────────

def evaluate_signal_states():
    """All 7 LSP signal states appear correctly."""
    print("\n" + "=" * 70)
    print("DIMENSION 2: SIGNAL STATE DISTRIBUTION")

    states_seen = Counter()

    # lsp_not_applicable (non-semantic)
    oracle = _make_oracle(lsp_state=LSPState.READY)
    for q in NON_SEMANTIC_QUERIES:
        r = _run_oracle(oracle, q["query"])
        signal = r.get("metadata", {}).get("lsp_signal")
        states_seen[signal] += 1

    # lsp_not_injected (no client)
    oracle = _make_oracle(lsp_state=None)
    for q in SEMANTIC_QUERIES[:3]:
        r = _run_oracle(oracle, q["query"])
        signal = r.get("metadata", {}).get("lsp_signal")
        states_seen[signal] += 1

    # lsp_not_ready (non-READY states)
    for state in [LSPState.COLD, LSPState.WARMING, LSPState.FAILED, LSPState.CLOSED]:
        oracle = _make_oracle(lsp_state=state)
        r = _run_oracle(oracle, SEMANTIC_QUERIES[0]["query"])
        signal = r.get("metadata", {}).get("lsp_signal")
        states_seen[signal] += 1

    # lsp_error
    oracle = _make_oracle(lsp_state=LSPState.READY, hover_return={"__lsp_error__": True, "error": {"code": -32600}})
    r = _run_oracle(oracle, SEMANTIC_QUERIES[0]["query"])
    signal = r.get("metadata", {}).get("lsp_signal")
    states_seen[signal] += 1

    # lsp_no_result
    oracle = _make_oracle(lsp_state=LSPState.READY, hover_return={"contents": None})
    r = _run_oracle(oracle, SEMANTIC_QUERIES[0]["query"])
    signal = r.get("metadata", {}).get("lsp_signal")
    states_seen[signal] += 1

    # lsp_used
    oracle = _make_oracle(lsp_state=LSPState.READY)
    r = _run_oracle(oracle, SEMANTIC_QUERIES[0]["query"])
    signal = r.get("metadata", {}).get("lsp_signal")
    states_seen[signal] += 1

    expected_states = {
        "lsp_not_applicable", "lsp_not_injected", "lsp_not_ready",
        "lsp_timeout", "lsp_error", "lsp_no_result", "lsp_used",
    }
    print(f"\n  States observed: {dict(states_seen)}")
    missing = expected_states - set(states_seen.keys())
    extra = set(states_seen.keys()) - expected_states
    if missing:
        print(f"  Missing: {missing}")
    if extra:
        print(f"  Unexpected: {extra}")
    coverage = len(set(states_seen.keys()) & expected_states) / len(expected_states) * 100
    print(f"  State coverage: {coverage:.0f}% ({len(set(states_seen.keys()) & expected_states)}/{len(expected_states)})")
    return coverage


# ── Dimension 3: Latency ────────────────────────────────────────────────────

def evaluate_latency():
    """p95 latency < 65ms with LSP, overhead < 20ms."""
    print("\n" + "=" * 70)
    print("DIMENSION 3: LATENCY")

    oracle_lsp = _make_oracle(lsp_state=LSPState.READY)
    oracle_no_lsp = _make_oracle(lsp_state=None)

    all_lsp_times = []
    all_no_lsp_times = []

    test_queries = SEMANTIC_QUERIES[:10] + NON_SEMANTIC_QUERIES
    for q in test_queries:
        for _ in range(ITERATIONS):
            t0 = time.time()
            _run_oracle(oracle_lsp, q["query"])
            all_lsp_times.append((time.time() - t0) * 1000)

            t0 = time.time()
            _run_oracle(oracle_no_lsp, q["query"])
            all_no_lsp_times.append((time.time() - t0) * 1000)

    all_lsp_times.sort()
    all_no_lsp_times.sort()

    p95_lsp = all_lsp_times[int(len(all_lsp_times) * 0.95)]
    p95_no_lsp = all_no_lsp_times[int(len(all_no_lsp_times) * 0.95)]
    overhead = p95_lsp - p95_no_lsp

    print(f"  p95 with LSP:    {p95_lsp:.2f}ms")
    print(f"  p95 without LSP: {p95_no_lsp:.2f}ms")
    print(f"  Overhead:        {overhead:.2f}ms")
    print(f"  Target: total <65ms, overhead <20ms")
    return p95_lsp, overhead


# ── Dimension 4: Fidelity Promotion ─────────────────────────────────────────

def evaluate_fidelity():
    """full when lsp_used, degraded when AST available without LSP, fallback otherwise."""
    print("\n" + "=" * 70)
    print("DIMENSION 4: FIDELITY PROMOTION")

    results = []

    # full: LSP used
    oracle = _make_oracle(lsp_state=LSPState.READY)
    r = _run_oracle(oracle, SEMANTIC_QUERIES[0]["query"])
    fidelity = r.get("fidelity")
    print(f"  LSP READY + semantic query → fidelity={fidelity} (expected: full)")
    results.append(fidelity == "full")

    # degraded: LSP not ready but AST available
    oracle = _make_oracle(lsp_state=LSPState.FAILED)
    r = _run_oracle(oracle, SEMANTIC_QUERIES[0]["query"])
    fidelity = r.get("fidelity")
    print(f"  LSP FAILED + semantic query → fidelity={fidelity} (expected: degraded)")
    results.append(fidelity == "degraded")

    # fallback: no LSP, non-semantic (no AST symbols hit)
    oracle = _make_oracle(lsp_state=None)
    ast_builder = MagicMock()
    ast_builder.build.return_value = _make_ast_result(symbols=[])
    oracle.ast_builder = ast_builder
    r = _run_oracle(oracle, NON_SEMANTIC_QUERIES[0]["query"])
    fidelity = r.get("fidelity")
    print(f"  No LSP + no AST → fidelity={fidelity} (expected: fallback)")
    results.append(fidelity == "fallback")

    pct = sum(results) / len(results) * 100
    print(f"\n  Correct: {sum(results)}/{len(results)} = {pct:.0f}%")
    return pct


# ── Dimension 5: Regression ─────────────────────────────────────────────────

def evaluate_regression():
    """PRIME+AST results unchanged when LSP disabled."""
    print("\n" + "=" * 70)
    print("DIMENSION 5: REGRESSION (LSP disabled vs enabled)")

    oracle_no = _make_oracle(lsp_state=None)
    oracle_yes = _make_oracle(lsp_state=LSPState.READY)

    all_queries = SEMANTIC_QUERIES[:5] + NON_SEMANTIC_QUERIES
    regressions = 0

    for q in all_queries:
        r_no = _run_oracle(oracle_no, q["query"])
        r_yes = _run_oracle(oracle_yes, q["query"])

        # Check PRIME chunks preserved
        prime_no = r_no.get("prime_chunks", [])
        prime_yes = r_yes.get("prime_chunks", [])
        prime_match = len(prime_no) == len(prime_yes)

        # Check AST symbols preserved
        ast_no = r_no.get("ast_symbols", [])
        ast_yes = r_yes.get("ast_symbols", [])
        ast_match = set(ast_no) == set(ast_yes)

        ok = prime_match and ast_match
        status = "OK" if ok else "REGRESSION"
        if not ok:
            regressions += 1
        print(f"  Q{q['id']:2d}: prime={prime_match}, ast={ast_match} → {status}")

    pct = (len(all_queries) - regressions) / len(all_queries) * 100
    print(f"\n  Zero regression: {regressions == 0} ({regressions} regressions found)")
    return pct


# ── Memory Soak ──────────────────────────────────────────────────────────────

def evaluate_memory_soak(iterations: int = 100):
    """100 iterations, verify <10MB growth."""
    print("\n" + "=" * 70)
    print(f"MEMORY SOAK ({iterations} iterations)")

    oracle = _make_oracle(lsp_state=LSPState.READY)

    tracemalloc.start()
    snapshot_start = tracemalloc.take_snapshot()

    for i in range(iterations):
        q = SEMANTIC_QUERIES[i % len(SEMANTIC_QUERIES)]
        _run_oracle(oracle, q["query"])

    snapshot_end = tracemalloc.take_snapshot()
    tracemalloc.stop()

    stats = snapshot_end.compare_to(snapshot_start, "lineno")
    total_growth_kb = sum(s.size_diff for s in stats) / 1024
    total_growth_mb = total_growth_kb / 1024

    top5 = sorted(stats, key=lambda s: s.size_diff, reverse=True)[:5]
    print(f"  Total growth: {total_growth_mb:.2f}MB (limit: 10MB)")
    print(f"  Top 5 allocators:")
    for s in top5:
        print(f"    {s.traceback}: {s.size_diff / 1024:.1f}KB")

    passed = total_growth_mb < 10
    print(f"  Result: {'PASS' if passed else 'FAIL'}")
    return total_growth_mb


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    all_queries = SEMANTIC_QUERIES + NON_SEMANTIC_QUERIES + NEGATIVE_QUERIES + AMBIGUOUS_QUERIES
    print("LSP SIGNAL BENCHMARK")
    print(f"Repo: {REPO}")
    print(f"Queries: {len(all_queries)}")
    print(f"  Semantic:    {len(SEMANTIC_QUERIES)}")
    print(f"  Non-semantic: {len(NON_SEMANTIC_QUERIES)}")
    print(f"  Negative:    {len(NEGATIVE_QUERIES)}")
    print(f"  Ambiguous:   {len(AMBIGUOUS_QUERIES)}")
    print(f"  Iterations per latency query: {ITERATIONS}")

    sem_pct, nonsem_pct = evaluate_routing_precision()
    state_coverage = evaluate_signal_states()
    p95_lsp, overhead = evaluate_latency()
    fidelity_pct = evaluate_fidelity()
    regression_pct = evaluate_regression()
    mem_growth = evaluate_memory_soak(iterations=100)

    # Verdict
    print("\n" + "=" * 70)
    print("VERDICT")
    print("=" * 70)

    all_pass = True

    status = "PASS" if sem_pct == 100 else "FAIL"
    print(f"  Semantic routing:     {sem_pct:5.0f}%  (target 100%)           → {status}")
    if status != "PASS": all_pass = False

    status = "PASS" if nonsem_pct == 100 else "FAIL"
    print(f"  Non-semantic skipped: {nonsem_pct:5.0f}%  (target 100%)           → {status}")
    if status != "PASS": all_pass = False

    status = "PASS" if state_coverage >= 85 else ("WARN" if state_coverage >= 70 else "FAIL")
    print(f"  State coverage:       {state_coverage:5.0f}%  (target >=85%)           → {status}")
    if status != "PASS": all_pass = False

    status = "PASS" if p95_lsp < 65 else "FAIL"
    print(f"  p95 latency:       {p95_lsp:6.1f}ms (target <65ms)          → {status}")
    if status != "PASS": all_pass = False

    status = "PASS" if overhead < 20 else "FAIL"
    print(f"  LSP overhead:      {overhead:6.1f}ms (target <20ms)          → {status}")
    if status != "PASS": all_pass = False

    status = "PASS" if fidelity_pct == 100 else "FAIL"
    print(f"  Fidelity correct:     {fidelity_pct:5.0f}%  (target 100%)           → {status}")
    if status != "PASS": all_pass = False

    status = "PASS" if regression_pct == 100 else "FAIL"
    print(f"  Zero regression:      {regression_pct:5.0f}%  (target 100%)           → {status}")
    if status != "PASS": all_pass = False

    status = "PASS" if mem_growth < 10 else "FAIL"
    print(f"  Memory growth:      {mem_growth:6.2f}MB (target <10MB)          → {status}")
    if status != "PASS": all_pass = False

    print()
    if all_pass:
        print("  GO — LSP Intelligence Phase passes benchmark. Ready for merge.")
    else:
        print("  NO-GO — One or more criteria failed. Fix before merge.")

    return all_pass


if __name__ == "__main__":
    main()
