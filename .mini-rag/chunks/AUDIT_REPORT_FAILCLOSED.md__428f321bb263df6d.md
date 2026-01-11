### E.4) Rollback Triggers (automáticos)

**Trigger 1: Test regression**
```bash
# In CI/pre-commit
pytest tests/ -v
if [ $? -ne 0 ]; then
  echo "❌ Tests failed - blocking merge"
  exit 1
fi
```

**Trigger 2: Performance degradation**
```bash
# In CI
result=$(uv run python scripts/bench_session_query.py)
p95=$(echo "$result" | jq -r '.p95_ms')

if [ $(echo "$p95 > 100" | bc) -eq 1 ]; then
  echo "❌ Performance regression: p95=${p95}ms > 100ms"
  exit 1
fi
```

**Trigger 3: Privacy leak**
```bash
# In CI
pytest tests/acceptance/test_no_privacy_leaks.py -v
if [ $? -ne 0 ]; then
  echo "❌ Privacy leak detected"
  exit 1
fi
```

**Manual Rollback**:
```bash
# Emergency: disable feature flag
export TRIFECTA_SESSION_JSONL=0

# Or git revert
git revert <commit-hash>
```

---
