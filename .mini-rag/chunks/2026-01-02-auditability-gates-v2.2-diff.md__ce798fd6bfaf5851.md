## D) PATCH: Integration test — Archivos canónicos reales

**Problema v2.1:** Nombres de archivos inventados (`prime_segment.md`, `session_segment.md`) pueden no coincidir con validación real.

**Diagnostic (para descubrir nombres canónicos):**

```bash
# 1. Encontrar validador de segmento
rg -n "validate.*segment|is_valid_segment|check_segment" src/ --type py

# 2. Encontrar archivos requeridos por el CLI
rg -n "skill\.md|agent\.md|prime|session" src/infrastructure/templates.py
rg -n "skill\.md|agent\.md|prime|session" src/infrastructure/file_system.py

# 3. Buscar en tests existentes qué archivos se usan
rg -n "\.md" tests/ -A 2 --type py | grep -E "(skill|agent|prime|session|README)"
```

**Resultado esperado de diagnóstico:**
- `skill.md` → requerido
- `agent.md` → requerido (o `README.md` en algunos casos)
- `prime_<segment>.md` → formato con nombre de segmento
- `session_<segment>.md` → formato con nombre de segmento

**v2.1 → v2.2 diff (reemplazar test):**
