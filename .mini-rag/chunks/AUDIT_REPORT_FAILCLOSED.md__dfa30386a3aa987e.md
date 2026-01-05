#### Step 6: Final Integration Test

**Run ALL tests**:
```bash
pytest tests/ -v --tb=short
# Target: 100% pass rate
```

**Manual smoke test**:
```bash
# 1. Append entry
uv run trifecta session append -s . --summary "V1 smoke test" --files "test.py" --commands "pytest"

# 2. Query (should return entry)
uv run trifecta session query -s . --last 1

# 3. Verify privacy
uv run trifecta session query -s . --last 1 | rg "/Users/" && echo "❌ LEAK" || echo "✅ CLEAN"

# 4. Benchmark
uv run python scripts/bench_session_query.py
# MUST: p95 < 100ms
```

---
