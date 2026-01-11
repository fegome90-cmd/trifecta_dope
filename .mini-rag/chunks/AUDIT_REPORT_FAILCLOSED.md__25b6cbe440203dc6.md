### D.2) Telemetry sanitization actual

**Código existente** (telemetry.py:L171):
```python
# Sanitize PII before persisting
payload = _sanitize_event(payload)
```

**Verificar qué hace `_sanitize_event`**:

```bash
$ rg "def _sanitize_event" src/infrastructure/telemetry.py -A 20
```

**Evidencia**: (necesito ver el código)

**BLOCKER #6**: Verificar que `_sanitize_event` cubre paths en `args` de `session.entry`

---
