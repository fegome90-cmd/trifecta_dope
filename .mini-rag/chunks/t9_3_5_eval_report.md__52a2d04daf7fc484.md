### 2. Single-Word Clamp: Missing Support Terms

**File**: `src/application/plan_use_case.py`

**Rule**:
```python
if best_is_single_word and not best_support_terms_present:
    return None, None, "weak_single_word_trigger", 0, None, debug_info
```

**Support Terms**:
```
{stats, metrics, events, event, latency, p95, p99, throughput,
 perf, performance, jsonl, events.jsonl, telemetry}
```

**Impact**: Single-word queries like "telemetry" now fall back when no support terms appear.
