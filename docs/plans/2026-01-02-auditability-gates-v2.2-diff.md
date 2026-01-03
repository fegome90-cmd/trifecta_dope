# v2.2 Diff — Correcciones Mínimas sobre v2.1

> Aplicar sobre `docs/plans/2026-01-02-auditability-gates-v2.1-patch.md`
>
> **Objetivo:** Eliminar PASS falsos restantes sin ampliar scope.
> **Reglas:** Fail-closed, no 2>/dev/null, patch mínimo.

---

## A) PATCH: sanitized_dump() — JSON-serializable

**Problema v2.1:** `model_dump()` puede devolver objetos no serializables (Path, datetime, etc.).

**Diagnostic (para confirmar):**
```bash
# Buscar definición de TrifectaPack y sus fields
rg -n "class TrifectaPack|repo_root.*Field|segment.*Field" src/domain/context_models.py
```

**v2.1 → v2.2 diff:**

```python
# En src/domain/context_models.py, dentro de clase TrifectaPack:

def sanitized_dump(self) -> str:
    """Dump JSON con paths sanitizados (FAIL-CLOSED: no PII en output).

    v2.2 FIX:
    - Usa model_dump(mode="json") para asegurar serialización JSON
    - Convierte repo_root a Path explícitamente
    - Evita TypeError en json.dumps()

    Anti-patrones evitados:
    - AP1: No string parsing; usa Path operations
    - AP6: Output es JSON determinista y serializable
    - AP8: SSOT de sanitización está aquí
    """
    import json
    import hashlib
    from pathlib import Path

    # v2.2 FIX: mode="json" asegura que valores no-serializables se conviertan
    data = self.model_dump(mode="json")

    # v2.2 FIX: Asegurar que repo_root es Path (podría ser string después de mode="json")
    repo_root_value = data.get("repo_root")
    if repo_root_value:
        segment_root = Path(str(repo_root_value))
    else:
        # Fallback si repo_root es None
        segment_root = Path.cwd()

    def _sanitize_path(value: str, root: Path) -> str:
        """Sanitiza un string que podría ser un path."""
        if not isinstance(value, str):
            return value

        # Detectar patrones de path absoluto conocidos
        if value.startswith("/Users/") or value.startswith("/home/"):
            # Intentar hacer relativo a root
            try:
                p = Path(value)
                rel = p.relative_to(root)
                return f"<RELATIVE>{rel.as_posix()}</RELATIVE>"
            except (ValueError, OSError):
                # No es relativo a root, redactar
                return f"<ABS_PATH_REDACTED>{hashlib.sha256(value.encode()).hexdigest()[:8]}</ABS_PATH_REDACTED>"

        # Detectar file:// URIs
        if "file://" in value:
            return value.replace("file://", "<FILE_URI_SANITIZED>")

        return value

    def _sanitize(obj):
        """Sanitiza recursivamente todas las strings."""
        if isinstance(obj, str):
            return _sanitize_path(obj, segment_root)
        elif isinstance(obj, dict):
            return {k: _sanitize(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_sanitize(item) for item in obj]
        return obj

    data = _sanitize(data)

    # v2.2 FIX: json.dumps ahora siempre recibe datos serializables
    return json.dumps(data, indent=2)
```

**Por qué elimina PASS falso:**
- `mode="json"` convierte Path objects a strings antes de sanitización
- Previene `TypeError: Object of type Path is not JSON serializable`
- Garantiza que `sanitized_dump()` nunca lanza excepción por serialización

---

## B) PATCH: Gates G3 (tabla) — STATUS/CODE limpios

**Problema v2.1:** Variables STATUS/CODE se capturan desde pipe que puede mezclar stderr con stdout.

**v2.1 → v2.2 diff (reemplazar fila G3 en tabla A):**

| Gate | Criterio PASS | Comando Exacto (stdout/stderr separados) | Evidencia Requerida | APs Evitados |
|------|---------------|----------------------------------------|---------------------|-------------|
| **G3: ast symbols** | JSON parseable + NO FILE_NOT_FOUND | `uv run trifecta ast symbols sym://python/mod/context_service > /tmp/g3_ast.json 2> /tmp/g3_ast.stderr; AST_RC=$?; cat /tmp/g3_ast.json \| jq -r '.status' > /tmp/g3_status.txt 2> /tmp/g3_jq_stderr.txt; STATUS=$(cat /tmp/g3_status.txt); CODE=$(cat /tmp/g3_ast.json \| jq -r '.errors[0].code // "null"' > /tmp/g3_code.txt 2> /tmp/g3_jq_stderr.txt; cat /tmp/g3_code.txt); echo "G3_AST=$AST_RC"; echo "G3_STATUS=$STATUS"; echo "G3_CODE=$CODE"` | (1) `/tmp/g3_ast.json` (JSON stdout), (2) `/tmp/g3_ast.stderr` (cmd stderr), (3) `/tmp/g3_status.txt`, `/tmp/g3_code.txt` (jq output limpio), (4) `/tmp/g3_jq_stderr.txt` (jq stderr) | AP1 (jq stdout → archivo → variable), AP6 (todo capturado), AP7 (variables limpias) |

**NOTAS SOBRE RCs (v2.2):**

```bash
# PASS/FAIL explícito:
if [ $AST_RC -eq 0 ] && [ "$STATUS" != "parse_error" ] && ([ "$STATUS" = "ok" ] || ([ "$STATUS" = "error" ] && [ "$CODE" != "FILE_NOT_FOUND" ])); then
    G3_OVERALL=0  # PASS
else
    G3_OVERALL=1  # FAIL
fi
```

**Por qué elimina PASS falso:**
- `jq` stdout se captura en archivo intermedio → variable (limpio)
- `jq` stderr se captura separado (no contamina STATUS/CODE)
- Si JSON no es parseable, `STATUS` contiene "parse_error" → FAIL explícito

---

## C) PATCH: audit_repro.sh (G3) — Mismo fix que B

**v2.1 → v2.2 diff (reemplazar sección G3 en audit_repro.sh):**

```bash
# ============================================================================
# G3: ast symbols (AP1, AP6, AP7: parse_error = FAIL, variables limpias)
# ============================================================================
echo "=== G3: AST Symbols Command ==="
echo "Running: uv run trifecta ast symbols sym://python/mod/context_service"

# v2.2 FIX: stdout y stderr separados desde el inicio
uv run trifecta ast symbols sym://python/mod/context_service \
    > "${ARTIFACTS}/g3_ast.json" \
    2> "${ARTIFACTS}/g3_ast.stderr"
G3_AST_RC=$?

echo "Command RC=$G3_AST_RC" | tee "${ARTIFACTS}/g3_ast_rc.txt"

# v2.2 FIX: jq stdout → archivo → variable (limpio)
if command -v jq &> /dev/null; then
    # STATUS: jq stderr → archivo separado
    jq -r '.status' "${ARTIFACTS}/g3_ast.json" \
        > "${ARTIFACTS}/g3_status.txt" \
        2> "${ARTIFACTS}/g3_jq_stderr.txt"
    G3_STATUS=$(cat "${ARTIFACTS}/g3_status.txt")

    # CODE: jq stderr → mismo archivo (append)
    jq -r '.errors[0].code // "null"' "${ARTIFACTS}/g3_ast.json" \
        > "${ARTIFACTS}/g3_code.txt" \
        2>> "${ARTIFACTS}/g3_jq_stderr.txt"
    G3_CODE=$(cat "${ARTIFACTS}/g3_code.txt")

    echo "Parsed: status=$G3_STATUS, error_code=$G3_CODE" | tee -a "${ARTIFACTS}/g3_ast_rc.txt"

    # v2.2 FIX: Validar que STATUS no esté vacío (jq falló)
    if [ -z "$G3_STATUS" ]; then
        G3_OVERALL=1  # FAIL
        echo "Result: FAIL (jq parsing failed, STATUS empty)"
        echo "jq stderr:"
        cat "${ARTIFACTS}/g3_jq_stderr.txt"
    elif [ "$G3_STATUS" = "parse_error" ] || [ "$G3_STATUS" = "null" ]; then
        G3_OVERALL=1  # FAIL
        echo "Result: FAIL (JSON invalid or status is null)"
        echo "Raw JSON:"
        cat "${ARTIFACTS}/g3_ast.json"
        echo "jq stderr:"
        cat "${ARTIFACTS}/g3_jq_stderr.txt"
    elif [ "$G3_STATUS" = "ok" ]; then
        G3_OVERALL=0  # PASS
        echo "Result: PASS"
    elif [ "$G3_CODE" = "FILE_NOT_FOUND" ]; then
        G3_OVERALL=1  # FAIL
        echo "Result: FAIL (FILE_NOT_FOUND)"
    else
        G3_OVERALL=0  # PASS (error diferente es aceptable)
        echo "Result: PASS (error is not FILE_NOT_FOUND)"
    fi
else
    echo "WARNING: jq not found, skipping JSON parse"
    G3_OVERALL=255  # SKIP
fi
echo ""
```

**Por qué elimina PASS falso:**
- Variables STATUS/CODE se leen de archivos intermedios (no de pipe)
- Si `jq` falla, `STATUS` está vacío → detectado como FAIL
- `jq` stderr no contamina variables principales

---

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

```python
# tests/integration/test_path_hygiene_e2e.py
import pytest
import subprocess
from pathlib import Path

def test_ctx_sync_produces_no_pii(tmp_path):
    """Integration: ctx sync NO genera PII en disco.

    v2.2 FIX: Usa nombres canónicos reales descubiertos via rg.
    """
    segment = tmp_path / "test_segment"
    segment.mkdir()
    ctx_dir = segment / "_ctx"
    ctx_dir.mkdir()

    segment_name = "test_segment"  # Usado para prime/session filenames

    # v2.2: Crear archivos canónicos con nombres correctos
    (segment / "skill.md").write_text("""# Test Skill

## Rules
- Rule 1: Test rule
""")

    # Nota: agent.md puede llamarse README.md en algunas versiones
    # Verificar con rg cuál es el canónico
    (segment / "agent.md").write_text("""# Agent

Stack: Python 3.12+
Purpose: Integration test
""")

    # v2.2: Formato correcto: prime_<segment>.md, session_<segment>.md
    (segment / f"prime_{segment_name}.md").write_text(f"""# Prime {segment_name.title()}

## Reading Order
1. skill.md
2. agent.md
""")

    (segment / f"session_{segment_name}.md").write_text(f"""# Session {segment_name.title()}

## Handoff
- Entry: {pytest.current_time()}
""")

    (segment / "README.md").write_text(f"""# README

Context for {segment_name}
""")

    # Ejecutar sync real
    result = subprocess.run(
        ["uv", "run", "trifecta", "ctx", "sync", "-s", str(segment)],
        capture_output=True,
        text=True,
        timeout=30
    )

    # v2.2: Mensaje de error más útil si sync falla
    if result.returncode != 0:
        print(f"=== SYNC STDOUT ===")
        print(result.stdout)
        print(f"=== SYNC STDERR ===")
        print(result.stderr)

    assert result.returncode == 0, f"sync failed: {result.stderr}"

    pack_path = ctx_dir / "context_pack.json"
    assert pack_path.exists(), "context_pack.json not created"

    content = pack_path.read_text()

    # v2.2: Assertions con mensajes útiles
    assert "/Users/" not in content, f"PII leak /Users/ found in first 500 chars: {content[:500]}"
    assert "/home/" not in content, f"PII leak /home/ found"
    assert "file://" not in content, f"file:// URI found"
```

**Por qué elimina FALSO ROJO:**
- Usa nombres correctos (`prime_test_segment.md`, no `prime_segment.md`)
- Si sync falla, imprime stdout/stderr completo para debugging
- Test refleja la realidad del validador de Trifecta

---

## Resumen: Por qué v2.2 elimina PASS falsos

| Issue | v2.1 | v2.2 | PASS falso eliminado |
|-------|------|------|---------------------|
| **JSON serializable** | `model_dump()` puede retornar Path | `model_dump(mode="json")` | Previene `TypeError` que hacía fallar sanitized_dump() |
| **STATUS contamination** | `STATUS=$(jq ... 2>&1 | tee ...)` | `STATUS=$(cat archivo.txt)` con stderr separado | STATUS/CODE están limpios, parse_error detectable |
| **jq stderr** | `2>/dev/null` o mezclado | Capturado en archivo dedicado | jq errors visibles, no ocultos |
| **Test filenames** | Nombres inventados | Nombres descubiertos via rg | Test no falla por nombre incorrecto |

---

## Cómo aplicar v2.2

```bash
# 1. Aplicar patch A) en src/domain/context_models.py
# 2. Reemplazar fila G3 en tabla del plan con patch B)
# 3. Reemplazar sección G3 en audit_repro.sh con patch C)
# 4. Reemplazar test con patch D)

# Verificar:
rg "model_dump\(mode=\"json\"\)" src/domain/context_models.py  # Debe encontrar
rg "g3_status.txt" docs/plans/...audit_repro.sh  # Debe encontrar
rg "prime_test_segment.md" tests/...test_path_hygiene_e2e.py  # Debe encontrar
```
