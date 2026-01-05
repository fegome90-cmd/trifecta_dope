### 📋 TICKET 1: Core Telemetry (2 hours)
**File:** `src/infrastructure/telemetry.py`

**Changes:**
1. Line 113: Extend `event()` to accept `**extra_fields`
2. Line 145: Merge extra_fields into payload dict
3. Line 245: Add AST/LSP/file_read summaries to `flush()`

**Tests:**
- `test_telemetry_extra_fields_serialized`
- `test_telemetry_summary_calculations`

**Verify:**
```bash
cd /workspaces/trifecta_dope
python -m pytest tests/unit/test_telemetry_ast_lsp.py::TestTelemetryExtension -v
```
