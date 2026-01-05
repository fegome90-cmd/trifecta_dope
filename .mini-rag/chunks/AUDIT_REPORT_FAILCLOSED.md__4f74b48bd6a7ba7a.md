```python
import time
import subprocess
import json
import numpy as np

def benchmark_session_query(dataset_size: int, iterations: int = 200):
    """Benchmark session query con dataset generado."""
    # Setup: generar dataset
    subprocess.run(["python", "scripts/generate_benchmark_dataset.py",
                    "--events", str(dataset_size)])

    latencies = []
    for _ in range(iterations):
        start = time.perf_counter()
        subprocess.run(["uv", "run", "trifecta", "session", "query",
                        "-s", ".", "--last", "5"],
                       capture_output=True, check=True)
        end = time.perf_counter()
        latencies.append((end - start) * 1000)  # ms

    p50 = np.percentile(latencies, 50)
    p95 = np.percentile(latencies, 95)
    p99 = np.percentile(latencies, 99)

    result = {
        "dataset_size": dataset_size,
        "iterations": iterations,
        "p50_ms": round(p50, 2),
        "p95_ms": round(p95, 2),
        "p99_ms": round(p99, 2),
        "max_ms": round(max(latencies), 2)
    }

    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    result = benchmark_session_query(dataset_size=10000)

    # GATE: p95 < 100ms
    if result["p95_ms"] > 100:
        print(f"❌ FAIL: p95={result['p95_ms']}ms > 100ms threshold")
        exit(1)
    print(f"✅ PASS: p95={result['p95_ms']}ms")
```
