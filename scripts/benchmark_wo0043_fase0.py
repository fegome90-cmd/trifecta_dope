"""Phase 0 Benchmark for WO-0043 — Kill Gate Evaluation.

Runs 20 queries against the existing GraphStore to validate:
1. Routing accuracy (does classify_query detect predicates correctly?)
2. Caller/callee recall (does the graph return useful results?)
3. Latency p95 (is graph query fast enough?)
"""

import time
import sys
from pathlib import Path

from src.domain.query_classifier import classify_query
from src.application.graph_service import GraphService
from src.domain.segment_resolver import resolve_segment_ref

# --- Query Sets ---
# Note: queries use symbols that exist in the current graph index.
# The oracle module was added after the last graph index, so we use
# older modules that have edges in the DB.
CALLER_QUERIES = [
    "who calls normalize_token",
    "callers of extract_imports",
    "quién llama al compute_projection_fingerprint",
    "quienes llaman a chunk_whole_file",
    "who calls ImportExtractor",
]

CALLEE_QUERIES = [
    "what does tokenize_description call",
    "callees of ImportExtractor",
    "qué llama compute_projection_fingerprint",
    "what does ContextService call",
    "qué llaman a GraphIndexer",
]

NO_RELACIONAL_QUERIES = [
    "how to configure the daemon",
    "what is context_pack.json",
    "show me the skill hub index",
    "explain the oracle architecture",
    "cómo se usa el comando ctx search",
]

AMBIGUOUS_QUERIES = [
    "context service",
    "graph store",
    "search query",
    "oracle result fidelity",
    "daemon lifecycle",
]


def run_benchmark():
    segment = Path.cwd()
    graph_svc = GraphService()

    results = {
        "routing": {"correct": 0, "total": 0},
        "caller_recall": {"found": 0, "total": 0},
        "callee_recall": {"found": 0, "total": 0},
        "latencies": [],
        "no_predicate_correct": 0,
        "no_predicate_total": 0,
    }

    print("=" * 70)
    print("WO-0043 Phase 0 Benchmark — Kill Gate")
    print("=" * 70)

    # --- CALLER QUERIES ---
    print("\n## CALLER QUERIES (5)")
    for q in CALLER_QUERIES:
        cls = classify_query(q)
        results["routing"]["total"] += 1
        if cls.predicate and cls.predicate.relation == "callers":
            results["routing"]["correct"] += 1
            target = cls.predicate.target
            t0 = time.time()
            try:
                res = graph_svc.callers(segment, target)
                lat = (time.time() - t0) * 1000
                results["latencies"].append(lat)
                nodes = res.get("nodes", [])
                if nodes:
                    results["caller_recall"]["found"] += 1
                    print(f"  ✅ '{q}' → {len(nodes)} callers ({lat:.1f}ms)")
                else:
                    print(f"  ⚠️  '{q}' → predicate detected, 0 callers ({lat:.1f}ms)")
            except Exception as e:
                lat = (time.time() - t0) * 1000
                results["latencies"].append(lat)
                print(f"  ❌ '{q}' → ERROR: {e} ({lat:.1f}ms)")
            results["caller_recall"]["total"] += 1
        else:
            print(f"  ❌ '{q}' → MISSED (predicate={cls.predicate})")

    # --- CALLEE QUERIES ---
    print("\n## CALLEE QUERIES (5)")
    for q in CALLEE_QUERIES:
        cls = classify_query(q)
        results["routing"]["total"] += 1
        if cls.predicate and cls.predicate.relation == "callees":
            results["routing"]["correct"] += 1
            target = cls.predicate.target
            t0 = time.time()
            try:
                res = graph_svc.callees(segment, target)
                lat = (time.time() - t0) * 1000
                results["latencies"].append(lat)
                nodes = res.get("nodes", [])
                if nodes:
                    results["callee_recall"]["found"] += 1
                    print(f"  ✅ '{q}' → {len(nodes)} callees ({lat:.1f}ms)")
                else:
                    print(f"  ⚠️  '{q}' → predicate detected, 0 callees ({lat:.1f}ms)")
            except Exception as e:
                lat = (time.time() - t0) * 1000
                results["latencies"].append(lat)
                print(f"  ❌ '{q}' → ERROR: {e} ({lat:.1f}ms)")
            results["callee_recall"]["total"] += 1
        else:
            print(f"  ❌ '{q}' → MISSED (predicate={cls.predicate})")

    # --- NO RELACIONAL QUERIES ---
    print("\n## NO-RELACIONAL QUERIES (5) — should NOT activate graph")
    for q in NO_RELACIONAL_QUERIES:
        cls = classify_query(q)
        results["no_predicate_total"] += 1
        if cls.predicate is None:
            results["no_predicate_correct"] += 1
            print(f"  ✅ '{q}' → no_predicate (correct)")
        else:
            print(f"  ❌ '{q}' → FALSE POSITIVE: {cls.predicate}")

    # --- AMBIGUOUS QUERIES ---
    print("\n## AMBIGUOUS QUERIES (5) — borderline")
    for q in AMBIGUOUS_QUERIES:
        cls = classify_query(q)
        results["routing"]["total"] += 1
        if cls.predicate is None:
            results["routing"]["correct"] += 1
            results["no_predicate_total"] += 1
            results["no_predicate_correct"] += 1
            print(f"  ✅ '{q}' → no_predicate (correct, conservative)")
        else:
            print(f"  ⚠️  '{q}' → detected: {cls.predicate} (false positive?)")

    # --- METRICS ---
    print("\n" + "=" * 70)
    print("BENCHMARK RESULTS")
    print("=" * 70)

    routing_acc = (results["routing"]["correct"] / results["routing"]["total"] * 100) if results["routing"]["total"] else 0
    caller_recall = (results["caller_recall"]["found"] / results["caller_recall"]["total"] * 100) if results["caller_recall"]["total"] else 0
    callee_recall = (results["callee_recall"]["found"] / results["callee_recall"]["total"] * 100) if results["callee_recall"]["total"] else 0
    np_acc = (results["no_predicate_correct"] / results["no_predicate_total"] * 100) if results["no_predicate_total"] else 0

    lats = sorted(results["latencies"]) if results["latencies"] else [0]
    p50 = lats[len(lats) // 2]
    p95_idx = int(len(lats) * 0.95)
    p95 = lats[min(p95_idx, len(lats) - 1)]
    avg = sum(lats) / len(lats) if lats else 0

    print(f"  Routing accuracy:    {routing_acc:.0f}% ({results['routing']['correct']}/{results['routing']['total']})")
    print(f"  Caller recall:       {caller_recall:.0f}% ({results['caller_recall']['found']}/{results['caller_recall']['total']})")
    print(f"  Callee recall:       {callee_recall:.0f}% ({results['callee_recall']['found']}/{results['callee_recall']['total']})")
    print(f"  No-predicate acc:    {np_acc:.0f}% ({results['no_predicate_correct']}/{results['no_predicate_total']})")
    print(f"  Latency avg:         {avg:.1f}ms")
    print(f"  Latency p50:         {p50:.1f}ms")
    print(f"  Latency p95:         {p95:.1f}ms")

    # --- KILL GATE ---
    print("\n" + "-" * 70)
    print("KILL GATE EVALUATION")
    print("-" * 70)
    kills = []
    if routing_acc < 95:
        kills.append(f"Routing accuracy {routing_acc:.0f}% < 95%")
    if p95 > 80:
        kills.append(f"Latency p95 {p95:.1f}ms > 80ms")

    if kills:
        print("  ❌ KILLED — do NOT proceed with WO-0043:")
        for k in kills:
            print(f"     - {k}")
        return 1
    else:
        print("  ✅ PASS — proceed with implementation")
        return 0


if __name__ == "__main__":
    sys.exit(run_benchmark())
