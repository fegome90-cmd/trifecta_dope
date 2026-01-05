### BLOCKER #6: Privacy Sanitization No Verificada
**Causa**: No se verificó que `_sanitize_event` cubre `args.files` de `session.entry`  
**Evidencia**: AUDIT:L497-L513  
**Fix mínimo**: Inspeccionar `_sanitize_event` (telemetry.py:L49) + test  
**Test/Gate**: `tests/acceptance/test_no_privacy_leaks.py -v`

---
