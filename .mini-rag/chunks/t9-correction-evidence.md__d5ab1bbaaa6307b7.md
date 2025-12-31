# === SERVICE CONCEPTS ===
  service: [ast_service, facade, api]
```

**Total:** 30 keys

### D.2 Proposed Refinement (+5 keys max)

**NO CHANGES PROPOSED**

**Rationale:**
- Current aliases already route to specific meta docs
- 30 keys is reasonable (< 200 limit)
- Adding more would not improve routing accuracy
- Focus should be on testing, not more aliases

---

## E) TESTS & METRICS

### E.1 Alias Expansion Tests

```bash
$ uv run pytest tests/unit/test_t9_alias_expansion.py -v
============================= test session starts ==============================
platform darwin -- Python 3.14.2, pytest-9.2, pluggy-1.6.0
cachedir: .pytest_cache
rootdir: /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope
configfile: pyproject.toml
plugins: cov-7.0.0
collecting ... collected 6 items

tests/unit/test_t9_alias_expansion.py::test_alias_expansion_increases_hits PASSED [ 16%]
tests/unit/test_t9_alias_expansion.py::test_alias_expansion_caps_terms PASSED [ 33%]
tests/unit/test_t9_alias_expansion.py::test_alias_expansion_dedupes_ids PASSED [ 50%]
tests/unit/test_t9_alias_expansion.py::test_telemetry_records_alias_fields PASSED [ 66%]
tests/unit/test_t9_alias_expansion.py::test_no_aliases_file_works_normally PASSED [ 83%]
tests/unit/test_t9_alias_expansion.py::test_alias_file_validation PASSED [100%]

============================== 6 passed in 0.03s ===============================
