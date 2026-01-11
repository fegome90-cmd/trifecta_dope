### BLOCKER #1: Dual Write Obligatorio (CRÍTICO)
**Causa**: Si V1 solo escribe a telemetry.jsonl → session.md deja de actualizarse → rompe 3 tests  
**Evidencia**: AUDIT:L196-L203  
**Fix mínimo**:
```python
# src/infrastructure/cli.py:session_append
telemetry.event(cmd="session.entry", ...)  # NEW
with open(session_file, "a") as f:  # KEEP
    f.write(entry_text)
```
**Test/Gate**: `pytest tests/unit/test_session_and_normalization.py -v` → MUST PASS 3/3

---
