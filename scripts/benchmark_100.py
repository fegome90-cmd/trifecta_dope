import time
import json
import subprocess
import statistics
from pathlib import Path

def run_cmd(cmd_list):
    start = time.time()
    result = subprocess.run(cmd_list, capture_output=True, text=True)
    latency = (time.time() - start) * 1000
    return latency, result.stdout, result.stderr

def run_benchmark(query="daemon", iterations=100):
    repo_path = Path(".").resolve()
    print(f"🚀 Starting Benchmark: 2 x {iterations} runs | Query: '{query}'")
    
    # Ensure daemon is running for Hybrid Dispatch
    print("🔄 Ensuring F1 Daemon is active...")
    subprocess.run(["uv", "run", "trifecta", "daemon", "stop"], capture_output=True)
    subprocess.run(["uv", "run", "trifecta", "daemon", "start", "--repo", str(repo_path)], capture_output=True)
    time.sleep(3) # Let it sync
    
    # --- 1. Traditional Search (via Hybrid Dispatch) ---
    print(f"📊 Running {iterations} iterations of 'ctx search'...")
    search_latencies = []
    search_hits = []
    for i in range(iterations):
        lat, out, err = run_cmd(["uv", "run", "trifecta", "ctx", "search", "--segment", ".", "--query", query])
        search_latencies.append(lat)
        try:
            hits = json.loads(out)
            search_hits.append(len(hits))
        except:
            search_hits.append(0)
        if (i+1) % 10 == 0: print(f"  Progress: {i+1}/{iterations}")

    # --- 2. Unified Oracle (Signal Fusion) ---
    print(f"🧠 Running {iterations} iterations of 'ctx oracle'...")
    oracle_latencies = []
    oracle_fidelities = []
    oracle_symbols = []
    for i in range(iterations):
        lat, out, err = run_cmd(["uv", "run", "trifecta", "ctx", "oracle", "--segment", ".", "--query", query])
        oracle_latencies.append(lat)
        try:
            res = json.loads(out)
            oracle_fidelities.append(res.get("fidelity", "unknown"))
            oracle_symbols.append(len(res.get("ast_symbols", [])))
        except:
            oracle_fidelities.append("error")
            oracle_symbols.append(0)
        if (i+1) % 10 == 0: print(f"  Progress: {i+1}/{iterations}")

    # Cleanup
    subprocess.run(["uv", "run", "trifecta", "daemon", "stop"], capture_output=True)

    # Analysis
    report = {
        "query": query,
        "iterations": iterations,
        "search": {
            "avg_ms": statistics.mean(search_latencies),
            "median_ms": statistics.median(search_latencies),
            "stdev": statistics.stdev(search_latencies),
            "p95_ms": statistics.quantiles(search_latencies, n=20)[18],
            "avg_hits": statistics.mean(search_hits)
        },
        "oracle": {
            "avg_ms": statistics.mean(oracle_latencies),
            "median_ms": statistics.median(oracle_latencies),
            "stdev": statistics.stdev(oracle_latencies),
            "p95_ms": statistics.quantiles(oracle_latencies, n=20)[18],
            "fidelity_distribution": {f: oracle_fidelities.count(f) for f in set(oracle_fidelities)},
            "avg_symbols": statistics.mean(oracle_symbols)
        }
    }

    print("\n" + "="*50)
    print("📈 BENCHMARK REPORT: F1 UNIFICATION")
    print("="*50)
    print(f"Search Avg Latency: {report['search']['avg_ms']:.2f}ms")
    print(f"Oracle Avg Latency: {report['oracle']['avg_ms']:.2f}ms")
    print(f"Overhead Ratio: {report['oracle']['avg_ms'] / report['search']['avg_ms']:.2f}x")
    print(f"Oracle Fidelity: {report['oracle']['fidelity_distribution']}")
    print(f"Avg Symbols/Oracle: {report['oracle']['avg_symbols']:.1f}")
    print("="*50)

    with open("docs/f1_benchmark_100_report.json", "w") as f:
        json.dump(report, f, indent=2)

if __name__ == "__main__":
    run_benchmark()
