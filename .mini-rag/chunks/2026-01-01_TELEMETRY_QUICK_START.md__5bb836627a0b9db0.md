### ✅ TICKET 4: Tests + Integration (16 hours)
**Files:** `tests/unit/test_telemetry_ast_lsp.py` + `tests/integration/test_lsp_instrumentation.py`

**Test coverage:**
- Monotonic clock verification
- Relative path redaction
- LSP READY trigger
- Fallback on timeout
- Bytes aggregation
- Summary percentile math
- Concurrent safety

**Run full suite:**
```bash
cd /workspaces/trifecta_dope
pytest tests/ --cov=src --cov-report=term-missing
# Target: >80% coverage
```

**Example: Validate percentiles work**
```bash
python -c "
from tests.fixtures.synthetic_telemetry import test_summary_percentile_validation
test_summary_percentile_validation()
print('✓ Percentile math validated')
"
```

---
