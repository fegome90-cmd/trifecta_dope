## A) PATCH: sanitized_dump() — JSON-serializable

**Problema v2.1:** `model_dump()` puede devolver objetos no serializables (Path, datetime, etc.).

**Diagnostic (para confirmar):**
```bash
# Buscar definición de TrifectaPack y sus fields
rg -n "class TrifectaPack|repo_root.*Field|segment.*Field" src/domain/context_models.py
```

**v2.1 → v2.2 diff:**
