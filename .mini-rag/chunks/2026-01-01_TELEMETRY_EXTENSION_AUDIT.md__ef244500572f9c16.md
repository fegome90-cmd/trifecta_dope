### N.2 Monotonic Clock Conversion

`time.perf_counter_ns()` returns nanoseconds. Convert to milliseconds as:
```python
elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
```

Store as **integer** in `timing_ms` field for backward compatibility.
