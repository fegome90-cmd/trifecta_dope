```

**Result:** ✅ NO code to index src/* by default

### B.2 Prohibition: Indexing src/* (MISSING - FAIL-CLOSED REQUIRED)

**Current State:** ❌ No explicit prohibition in code

**Required Fix:** Add fail-closed check in `ingest_trifecta.py`

```python
