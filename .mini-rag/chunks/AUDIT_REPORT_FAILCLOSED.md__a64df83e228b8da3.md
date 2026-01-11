###B.2) Backward Compatibility Gates

**Tests actuales que NO deben romperse**:

1. `test_session_append_creates_file` - Debe seguir creando session.md
2. `test_session_append_appends_second_entry` - Debe seguir appendeando
3. `test_session_append_includes_pack_sha_when_present` - Debe incluir pack_sha

**RISK**: Si V1 solo escribe a telemetry.jsonl, estos 3 tests **FALLAN**

**FIX**: V1 debe escribir a AMBOS destinos (dual write):
```python
# 1. Write to telemetry (new)
telemetry.event(cmd="session.entry", args={...}, result={...}, timing_ms=0)

# 2. Write to session.md (existing - keep for backward compat)
with open(session_file, "a") as f:
    f.write(entry_text)
```

**TEST GATE**: Ejecutar `pytest tests/unit/test_session_and_normalization.py -v` DEBE pasar al 100%

---
