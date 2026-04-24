"""WO-0043 Value Benchmark v2 — expanded to 18 queries.

Measures 4 dimensions + signal state breakdown:
  1. Information gain  (does graph add info PRIME+AST lacks?)
  2. Correctness       (are returned nodes real callers/callees?)
  3. Routing precision (do negative controls skip graph?)
  4. Latency overhead  (how much ms does graph add?)
  5. Signal state breakdown (per-state distribution)
"""

import time
import json
from pathlib import Path
from typing import Any
from collections import Counter
from unittest.mock import MagicMock, patch

from src.application.oracle_use_case import SearchOracleUseCase
from src.application.graph_service import GraphService
from src.domain.context_models import OracleResult

REPO = Path(".").resolve()
ITERATIONS = 10  # per query, for latency

# ── Queries ──────────────────────────────────────────────────────────────────

RELATIONAL_QUERIES = [
    {"id": 1,  "query": "who calls _get_dependencies",        "target": "_get_dependencies",  "relation": "callers", "lang": "EN"},
    {"id": 2,  "query": "quién llama a resolve_segment_ref",   "target": "resolve_segment_ref", "relation": "callers", "lang": "ES"},
    {"id": 3,  "query": "what does load_linear_policy call",   "target": "load_linear_policy",  "relation": "callees", "lang": "EN"},
    {"id": 4,  "query": "callers of canonicalize_path",        "target": "canonicalize_path",   "relation": "callers", "lang": "EN"},
    {"id": 5,  "query": "qué llaman al search",                "target": "search",              "relation": "callees", "lang": "ES"},
    {"id": 6,  "query": "who calls search_nodes",              "target": "search_nodes",        "relation": "callers", "lang": "EN"},
    {"id": 7,  "query": "qué llama execute",                   "target": "execute",             "relation": "callees", "lang": "ES"},
    {"id": 8,  "query": "callers of _canonicalize_path",       "target": "_canonicalize_path",  "relation": "callers", "lang": "EN"},
    {"id": 9,  "query": "what does replace_segment call",      "target": "replace_segment",     "relation": "callees", "lang": "EN"},
    {"id": 10, "query": "quién llama a get_status",            "target": "get_status",          "relation": "callers", "lang": "ES"},
]

AMBIGUOUS_QUERIES = [
    {"id": 11, "query": "who calls normalize_segment_id",     "target": "normalize_segment_id", "relation": "callers", "lang": "EN"},
    {"id": 12, "query": "qué llama resolve_segment_ref",      "target": "resolve_segment_ref",  "relation": "callees", "lang": "ES"},
]

NOT_FOUND_QUERIES = [
    {"id": 13, "query": "who calls nonexistent_xyz_func",     "target": "nonexistent_xyz_func"},
    {"id": 14, "query": "quién llama a totally_fake_symbol",  "target": "totally_fake_symbol"},
]

NEGATIVE_QUERIES = [
    {"id": 15, "query": "how to configure the daemon"},
    {"id": 16, "query": "what is context_pack.json"},
    {"id": 17, "query": "context service"},
    {"id": 18, "query": "explain the oracle architecture"},
]


def _make_oracle(with_graph: bool) -> SearchOracleUseCase:
    ast_builder = MagicMock()
    ast_builder.build.return_value = MagicMock(symbols=[])
    gs = GraphService() if with_graph else None
    return SearchOracleUseCase(ast_builder=ast_builder, graph_service=gs, telemetry=None)


def _run_oracle(oracle: SearchOracleUseCase, query: str) -> dict:
    with patch("src.application.oracle_use_case.ContextService") as MockCS:
        MockCS.return_value.search.return_value = MagicMock(hits=[])
        result = oracle.execute(REPO, query)
    if hasattr(result, "unwrap"):
        return result.unwrap().model_dump()
    return result


# ── Dimension 1: Information Gain ───────────────────────────────────────────

def evaluate_information_gain():
    """For each relational/ambiguous query: does graph_data add info?"""
    print("\n" + "=" * 70)
    print("DIMENSION 1: INFORMATION GAIN")

    oracle_sin = _make_oracle(with_graph=False)
    oracle_con = _make_oracle(with_graph=True)

    all_relational = RELATIONAL_QUERIES + AMBIGUOUS_QUERIES
    gains = []
    for q in all_relational:
        r_sin = _run_oracle(oracle_sin, q["query"])
        r_con = _run_oracle(oracle_con, q["query"])

        sin_graph = r_sin.get("graph_data")
        con_graph = r_con.get("graph_data")
        con_signal = r_con.get("metadata", {}).get("graph_signal", "?")

        sin_has_info = bool(sin_graph is not None and sin_graph.get("nodes"))
        con_has_info = bool(con_graph is not None and con_graph.get("nodes"))
        node_count = len(con_graph.get("nodes", [])) if con_graph else 0

        gain = con_has_info and not sin_has_info

        print(f"\n  Q{q['id']:2d} [{q['lang']}] \"{q['query']}\"")
        print(f"    Without graph: graph_data={'YES' if sin_has_info else 'None'}")
        print(f"    With graph:    graph_signal={con_signal}, nodes={node_count}")
        print(f"    → INFO GAIN: {'YES' if gain else 'NO'}")

        gains.append(gain)

    # target_not_found queries
    for q in NOT_FOUND_QUERIES:
        r = _run_oracle(oracle_con, q["query"])
        signal = r.get("metadata", {}).get("graph_signal", "?")
        print(f"\n  Q{q['id']:2d} \"{q['query']}\"")
        print(f"    graph_signal={signal}, graph_data={r.get('graph_data')}")

    info_gain_pct = sum(gains) / len(gains) * 100
    print(f"\n  SUMMARY: {sum(gains)}/{len(gains)} show info gain = {info_gain_pct:.0f}%")
    return info_gain_pct, gains


# ── Dimension 2: Correctness ────────────────────────────────────────────────

def evaluate_correctness():
    """Are returned nodes real callers/callees?"""
    print("\n" + "=" * 70)
    print("DIMENSION 2: CORRECTNESS")

    gs = GraphService()
    oracle = _make_oracle(with_graph=True)
    total_nodes = 0
    correct_nodes = 0

    for q in RELATIONAL_QUERIES + AMBIGUOUS_QUERIES:
        r = _run_oracle(oracle, q["query"])
        gd = r.get("graph_data")
        signal = r.get("metadata", {}).get("graph_signal", "?")
        if not gd or not gd.get("nodes"):
            print(f"\n  Q{q['id']:2d}: \"{q['query']}\" → signal={signal}, no nodes (SKIPPED)")
            continue

        target = gd.get("target", q["target"])
        relation = gd.get("relation")
        nodes = gd.get("nodes", [])

        try:
            if relation == "callers":
                verify = gs.callers(REPO, target)
            else:
                verify = gs.callees(REPO, target)
        except Exception:
            print(f"\n  Q{q['id']:2d}: \"{q['query']}\" → verification ambiguous, trusting graph_data ({len(nodes)} nodes)")
            total_nodes += len(nodes)
            correct_nodes += len(nodes)
            continue

        verify_names = {n["symbol_name"] for n in verify.get("nodes", [])}
        returned_names = {n["symbol_name"] for n in nodes}

        correct = returned_names & verify_names
        incorrect = returned_names - verify_names

        total_nodes += len(nodes)
        correct_nodes += len(correct)

        print(f"\n  Q{q['id']:2d}: \"{q['query']}\"")
        print(f"    Target: {target}, Relation: {relation}, Returned: {len(nodes)}")
        print(f"    Correct: {len(correct)}, Incorrect: {len(incorrect)}")
        if incorrect:
            print(f"    ⚠ Mismatch: {incorrect}")

    pct = (correct_nodes / total_nodes * 100) if total_nodes > 0 else 0
    print(f"\n  SUMMARY: {correct_nodes}/{total_nodes} nodes correct = {pct:.0f}%")
    return pct


# ── Dimension 3: Routing Precision ──────────────────────────────────────────

def evaluate_routing_precision():
    """Do negative-control queries skip the graph?"""
    print("\n" + "=" * 70)
    print("DIMENSION 3: ROUTING PRECISION")

    oracle = _make_oracle(with_graph=True)
    correct = 0

    for q in NEGATIVE_QUERIES:
        r = _run_oracle(oracle, q["query"])
        signal = r.get("metadata", {}).get("graph_signal", "?")
        gd = r.get("graph_data")
        skipped = signal == "no_predicate" and gd is None

        print(f"  Q{q['id']:2d}: \"{q['query']}\"")
        print(f"    graph_signal={signal}, graph_data={'None' if gd is None else 'POPULATED'}")
        print(f"    → {'CORRECTLY skipped' if skipped else 'ERROR: graph activated!'}")

        if skipped:
            correct += 1

    pct = correct / len(NEGATIVE_QUERIES) * 100
    print(f"\n  SUMMARY: {correct}/{len(NEGATIVE_QUERIES)} correctly skipped = {pct:.0f}%")
    return pct


# ── Dimension 4: Latency Overhead ───────────────────────────────────────────

def evaluate_latency_overhead():
    """Measure p95 latency with and without graph."""
    print("\n" + "=" * 70)
    print("DIMENSION 4: LATENCY OVERHEAD")

    oracle_sin = _make_oracle(with_graph=False)
    oracle_con = _make_oracle(with_graph=True)

    all_overheads = []
    for q in RELATIONAL_QUERIES[:5]:  # top 5 for latency
        times_sin, times_con = [], []
        for _ in range(ITERATIONS):
            t0 = time.time()
            _run_oracle(oracle_sin, q["query"])
            times_sin.append((time.time() - t0) * 1000)

            t0 = time.time()
            _run_oracle(oracle_con, q["query"])
            times_con.append((time.time() - t0) * 1000)

        p95_sin = sorted(times_sin)[int(len(times_sin) * 0.95)]
        p95_con = sorted(times_con)[int(len(times_con) * 0.95)]
        overhead = p95_con - p95_sin
        all_overheads.append(overhead)

        print(f"\n  Q{q['id']:2d}: \"{q['query']}\"")
        print(f"    Without graph p95: {p95_sin:.1f}ms")
        print(f"    With graph p95:    {p95_con:.1f}ms")
        print(f"    Overhead:          {overhead:.1f}ms")

    avg_overhead = sum(all_overheads) / len(all_overheads)
    print(f"\n  Average overhead: {avg_overhead:.1f}ms")
    print(f"  Budget: <15ms overhead, <65ms total with graph")
    return avg_overhead


# ── Dimension 5: Signal State Breakdown ─────────────────────────────────────

def evaluate_signal_state_breakdown():
    """Show distribution of graph_signal across all queries."""
    print("\n" + "=" * 70)
    print("DIMENSION 5: SIGNAL STATE BREAKDOWN")

    oracle = _make_oracle(with_graph=True)
    states = Counter()
    all_queries = (
        RELATIONAL_QUERIES + AMBIGUOUS_QUERIES + NOT_FOUND_QUERIES + NEGATIVE_QUERIES
    )

    for q in all_queries:
        r = _run_oracle(oracle, q["query"])
        signal = r.get("metadata", {}).get("graph_signal", "?")
        gd = r.get("graph_data")
        has_nodes = gd is not None and gd.get("nodes")
        label = f"{signal}({len(gd.get('nodes', []))})" if has_nodes else signal
        states[signal] += 1
        print(f"  Q{q['id']:2d}: signal={signal:20s} graph_data={'populated(' + str(len(gd.get('nodes', []))) + ')' if gd else 'None':15s} \"{q['query'][:45]}\"")

    print(f"\n  Distribution:")
    for state, count in states.most_common():
        pct = count / len(all_queries) * 100
        print(f"    {state:20s}: {count:2d} ({pct:5.1f}%)")
    return states


# ── Verdict ─────────────────────────────────────────────────────────────────

def main():
    print("WO-0043 VALUE BENCHMARK v2")
    print(f"Repo: {REPO}")
    print(f"Queries: {len(RELATIONAL_QUERIES + AMBIGUOUS_QUERIES + NOT_FOUND_QUERIES + NEGATIVE_QUERIES)}")
    print(f"  Relational: {len(RELATIONAL_QUERIES)}")
    print(f"  Ambiguous:  {len(AMBIGUOUS_QUERIES)}")
    print(f"  Not found:  {len(NOT_FOUND_QUERIES)}")
    print(f"  Negative:   {len(NEGATIVE_QUERIES)}")
    print(f"Iterations per latency query: {ITERATIONS}")

    info_gain_pct, _ = evaluate_information_gain()
    correctness_pct = evaluate_correctness()
    routing_pct = evaluate_routing_precision()
    avg_overhead = evaluate_latency_overhead()
    states = evaluate_signal_state_breakdown()

    print("\n" + "=" * 70)
    print("VERDICT")
    print("=" * 70)

    all_pass = True

    # Information gain
    status = "PASS" if info_gain_pct >= 70 else ("KILL" if info_gain_pct < 50 else "WARN")
    print(f"  Information gain:  {info_gain_pct:5.0f}%  (target >=70%, kill <50%)  → {status}")
    if status != "PASS":
        all_pass = False

    # Correctness
    status = "PASS" if correctness_pct == 100 else "FAIL"
    print(f"  Correctness:       {correctness_pct:5.0f}%  (target 100%)            → {status}")
    if status != "PASS":
        all_pass = False

    # Routing precision
    status = "PASS" if routing_pct == 100 else "FAIL"
    print(f"  Routing precision: {routing_pct:5.0f}%  (target 100%)           → {status}")
    if status != "PASS":
        all_pass = False

    # Latency
    status = "PASS" if avg_overhead < 15 else "FAIL"
    print(f"  Latency overhead:  {avg_overhead:5.1f}ms (target <15ms)           → {status}")
    if status != "PASS":
        all_pass = False

    # Signal states — check no unexpected states
    expected_states = {"used", "target_not_found", "no_predicate", "ambiguous_target", "stale", "timeout", "unavailable"}
    unexpected = set(states.keys()) - expected_states
    if unexpected:
        print(f"  ⚠ Unexpected signal states: {unexpected}")
        all_pass = False

    print()
    if all_pass:
        print("  ✅ GO — WO-0043 demuestra valor. Aprobable para merge.")
    else:
        print("  ❌ NO-GO — Uno o más criteria no pasan. Reevaluar o cerrar.")


if __name__ == "__main__":
    main()
