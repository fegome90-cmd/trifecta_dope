### Rule #1: Monotonic Timing
```python
# ✅ DO THIS:
start_ns = time.perf_counter_ns()
operation()
elapsed_ms = int((time.perf_counter_ns() - start_ns) / 1_000_000)

# ❌ DON'T DO THIS:
start_time = time.time()
operation()
elapsed_ms = int((time.time() - start_time) * 1000)  # Can jump backward!
```
