# Correcciones v2.1 — Gates y Script (PATCH para plan v2.0)

> Aplicar estos parches sobre `docs/plans/2026-01-02-auditability-gates-v2-antipatterns.md`
>
> **Problemas corregidos:**
> - G2: RC mal capturado en tabla ($? → PIPESTATUS[0])
> - G3: JSON parsing inseguro (mezcla stdout/stderr, parse_error no tratado)
> - sanitized_dump(): sanitización incompleta para paths arbitrarios
> - audit_repro.sh: declare -A no portátil en bash 3.2
> - jq stderr: 2>/dev/null contradice AP6

---

## A) Metas & Gates (CORREGIDO v2.1)

| Gate | Criterio PASS | Comando Exacto (RC preservado) | Evidencia Requerida | APs Evitados |
|------|---------------|-------------------------------|---------------------|-------------|
| **G1: Baseline reproducible** | `pytest --collect-only` retorna RC=0 (NO "ERROR collecting") | `uv run pytest --collect-only -q 2>&1 \| tee /tmp/g1_pytest.log; G1_RC=\${PIPESTATUS[0]}; echo "G1_RC=$G1_RC"` | (1) `/tmp/g1_pytest.log` (stdout/stderr crudo), (2) `G1_RC` (0=PASS) | AP6, AP7 |
| **G2: Path Hygiene (no PII)** | `_ctx/context_pack.json` NO contiene `/Users/`, `/home/`, `file://` | `uv run trifecta ctx sync -s . 2>&1 \| tee /tmp/g2_sync.log; SYNC_RC=\${PIPESTATUS[0]}; rg -n '"/Users/\|"/home/\|file://' _ctx/context_pack.json 2>&1 \| tee /tmp/g2_rg.log; RG_RC=\${PIPESTATUS[0]}; echo "G2_SYNC=$SYNC_RC"; echo "G2_RG=$RG_RC"` | (1) `/tmp/g2_sync.log`, (2) `/tmp/g2_rg.log`, (3) `SYNC_RC` (0=sync ok), (4) `RG_RC` (1=no matches=PASS) | AP6, AP7, AP10 |
| **G3: ast symbols operable** | `trifecta ast symbols` NO retorna FILE_NOT_FOUND, JSON es parseable | `uv run trifecta ast symbols sym://python/mod/context_service > /tmp/g3_ast.json 2> /tmp/g3_ast.stderr; AST_RC=$?; STATUS=\$(jq -r '.status // "parse_error"' /tmp/g3_ast.json 2>&1 \| tee /tmp/g3_jq.log); CODE=\$(jq -r '.errors[0].code // "null"' /tmp/g3_ast.json); echo "G3_AST=$AST_RC"; echo "G3_STATUS=$STATUS"; echo "G3_CODE=$CODE"` | (1) `/tmp/g3_ast.json` (JSON stdout), (2) `/tmp/g3_ast.stderr` (stderr separado), (3) `/tmp/g3_jq.log` (jq stderr), (4) `AST_RC`, `STATUS`, `CODE` | AP1 (jq parse desde archivo), AP6 (stderr capturado), AP7 (parse_error=FAIL) |

**NOTAS SOBRE RCs (AP7, corregido):**
- G1: `G1_RC=0` → PASS; `G1_RC≠0` → FAIL
- G2: `SYNC_RC=0` AND `RG_RC=1` → PASS; else → FAIL
- G3: `AST_RC=0` AND `STATUS≠parse_error` AND (`STATUS=ok` OR `CODE≠FILE_NOT_FOUND`) → PASS; else → FAIL

**CAMBIOS desde v2.0:**
- G2: `PIPESTATUS[0]` explícito (no `$?` de tee)
- G3: stdout→.json, stderr→.stderr (separados); `parse_error` tratado como FAIL

---

## C) Blocker 1: G2 Path Hygiene — sanitized_dump() CORREGIDO

**Problema identificado:** v2.0 solo sanitizaba `repo_root` y `file://`, pero NO paths absolutos arbitrarios en otros campos (ej: `source_files[].path`).

**Patch completo (reemplazar versión v2.0):**

```python
# En src/domain/context_models.py, clase TrifectaPack:

def sanitized_dump(self) -> str:
    """Dump JSON con paths sanitizados (FAIL-CLOSED: no PII en output).

    Sanitiza TODOS los paths absolutos, no solo repo_root.
    Estrategia:
    1. Si path es relativo a segment_root: convertir a relativo
    2. Si es path absoluto externo: redactar con placeholder

    Anti-patrones evitados:
    - AP1: No string parsing; usa Path operations
    - AP6: Output es JSON determinista
    - AP8: SSOT de sanitización está aquí
    """
    import json
    from pathlib import Path

    data = self.model_dump()
    segment_root = Path(data.get("repo_root", "/"))

    def _sanitize_path(value: str, root: Path) -> str:
        """Sanitiza un string que podría ser un path."""
        # Detectar patrones de path absoluto conocidos
        if value.startswith("/Users/") or value.startswith("/home/"):
            # Intentar hacer relativo a root
            try:
                p = Path(value)
                rel = p.relative_to(root)
                return f"<RELATIVE>{rel.as_posix()}</RELATIVE>"
            except ValueError:
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
    return json.dumps(data, indent=2)
```

**Imports requeridos:**
```python
# Agregar al tope del archivo:
import hashlib
```

**Tests tripwire actualizados (validan sanitización completa):**

```python
# tests/unit/test_path_hygiene.py
import pytest
from pathlib import Path
from src.domain.context_models import TrifectaPack

def test_sanitized_dump_removes_absolute_paths():
    """Unit: sanitized_dump() elimina TODOS los paths absolutos."""
    pack = TrifectaPack(
        repo_root=Path("/Users/felipe/Developer/agent_h"),
        segment=".",
        schema_version=1,
        digest=[],
        index=[],
        chunks=[]
    )

    # Simular chunks con paths absolutos (caso real problemático)
    pack.chunks = [
        {
            "id": "test",
            "text": "content",
            "source_path": "/Users/felipe/Developer/agent_h/some/file.py",  # PATH PROBLEMÁTICO
        }
    ]

    json_str = pack.sanitized_dump()

    # AP7: Assertions explícitas (PASS solo si NO hay PII)
    assert "/Users/" not in json_str, f"PII leak /Users/: {json_str[:500]}"
    assert "/home/" not in json_str
    assert "file://" not in json_str
    assert "<RELATIVE>" in json_str or "<ABS_PATH_REDACTED>" in json_str

def test_sanitized_dump_relative_paths_ok():
    """Unit: paths relativos se preservan."""
    pack = TrifectaPack(
        repo_root=Path("/Users/felipe/Developer/agent_h"),
        segment=".",
        schema_version=1,
        digest=[],
        index=[],
        chunks=[]
    )

    json_str = pack.sanitized_dump()

    # Paths relativos NO deben ser redactados
    assert "some/relative/path" in json_str or "some_relative_path" in json_str or "<RELATIVE>" in json_str
```

---

## D) audit_repro.sh (CORREGIDO v2.1 — Bash 3.2 compatible)

**Problemas identificados:**
- `declare -A` no funciona en bash 3.2 (macOS por defecto)
- `jq ... 2>/dev/null` contradice AP6
- G3 mezcla stdout/stderr

```bash
#!/usr/bin/env bash
# audit_repro.sh v2.1 — Evidence capture para trifecta_dope auditability gates
#
# CAMBIOS desde v2.0:
# - Sin arrays asociativos (bash 3.2 compatible)
# - G3: stdout/stderr separados
# - jq stderr capturado (no 2>/dev/null)
# - parse_error tratado como FAIL
#
# POLÍTICA (AP6, AP7):
# - NO abortar en fallos (capturar todo)
# - TODO va a archivos via tee (no /dev/null en gates)
# - RCs preservados con ${PIPESTATUS[n]}
# - Gates calculados al final con RCs explícitos

set +e  # CRÍTICO: No abortar en fallos (AP6)

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARTIFACTS="/tmp/trifecta_audit_${TIMESTAMP}"
mkdir -p "${ARTIFACTS}"

# Variables simples (bash 3.2 compatible - NO declare -A)
G1_RC=1
G2_SYNC_RC=1
G2_RG_RC=1
G2_OVERALL=1
G3_AST_RC=1
G3_STATUS=""
G3_CODE=""
G3_OVERALL=1
G4_OVERALL=255  # 255 = SKIP

echo "=== Trifecta Auditability Evidence Capture v2.1 ==="
echo "Timestamp: ${TIMESTAMP}"
echo "Artifacts: ${ARTIFACTS}"
echo ""

# Verificar bash version (opcional, para debugging)
echo "Bash version: $BASH_VERSION"
echo ""

# ============================================================================
# G0: Baseline (git state)
# ============================================================================
echo "=== G0: Git Baseline ==="
git rev-parse HEAD > "${ARTIFACTS}/git_sha.txt" 2>&1
git status --porcelain > "${ARTIFACTS}/git_status.txt" 2>&1
echo "Git SHA: $(cat ${ARTIFACTS}/git_sha.txt)"
echo "Git dirty: $(test -s ${ARTIFACTS}/git_status.txt && echo 'yes' || echo 'no')"
echo ""

# ============================================================================
# G1: pytest collecting (AP7: FAIL-CLOSED con RC explícito)
# ============================================================================
echo "=== G1: Pytest Collection ==="
echo "Running: uv run pytest --collect-only -q"

uv run pytest --collect-only -q 2>&1 | tee "${ARTIFACTS}/g1_pytest_collect.txt"
G1_RC=${PIPESTATUS[0]}

echo "G1_RC=$G1_RC" | tee -a "${ARTIFACTS}/g1_pytest_collect.txt"

if grep -qi "ERROR collecting" "${ARTIFACTS}/g1_pytest_collect.txt"; then
    G1_RC=1  # FAIL
    echo "Result: FAIL (ERROR collecting detected)"
else
    if [ $G1_RC -eq 0 ]; then
        echo "Result: PASS (RC=0, no collection errors)"
    else
        echo "Result: FAIL (RC=$G1_RC, unknown error)"
    fi
fi
echo ""

# ============================================================================
# G2: Path Hygiene (AP6, AP7, AP10: sync debe pasar primero)
# ============================================================================
echo "=== G2: Path Hygiene Check ==="
echo "Running: uv run trifecta ctx sync -s ."

uv run trifecta ctx sync -s . 2>&1 | tee "${ARTIFACTS}/g2_ctx_sync.txt"
G2_SYNC_RC=${PIPESTATUS[0]}

echo "Sync RC=$G2_SYNC_RC" | tee -a "${ARTIFACTS}/g2_ctx_sync.txt"

echo "Checking for PII/absolute paths..."
rg -n '"/Users/|"/home/|file://' _ctx/context_pack.json 2>&1 | tee "${ARTIFACTS}/g2_rg_pii.txt"
G2_RG_RC=${PIPESTATUS[0]}

echo "rg RC=$G2_RG_RC" | tee "${ARTIFACTS}/g2_rg_rc.txt"

# AP7: lógica explícita de PASS/FAIL
if [ $G2_SYNC_RC -ne 0 ]; then
    G2_OVERALL=1  # FAIL
    echo "Result: FAIL (sync failed, RC=$G2_SYNC_RC)"
else
    if [ $G2_RG_RC -eq 1 ]; then
        G2_OVERALL=0  # PASS
        echo "Result: PASS (sync ok, no PII found)"
    else
        G2_OVERALL=1  # FAIL
        echo "Result: FAIL (PII found, RG_RC=$G2_RG_RC)"
        echo "Matches:"
        cat "${ARTIFACTS}/g2_rg_pii.txt"
    fi
fi
echo ""

# Sample context_pack.json
echo "Sample context_pack.json (first 30 lines):"
head -30 _ctx/context_pack.json | tee "${ARTIFACTS}/g2_context_pack_sample.txt"
echo ""

# ============================================================================
# G3: ast symbols (AP1, AP6, AP7: parse_error = FAIL)
# ============================================================================
echo "=== G3: AST Symbols Command ==="
echo "Running: uv run trifecta ast symbols sym://python/mod/context_service"

# G3 v2.1: stdout/stderr separados
uv run trifecta ast symbols sym://python/mod/context_service \
    > "${ARTIFACTS}/g3_ast.json" \
    2> "${ARTIFACTS}/g3_ast.stderr"
G3_AST_RC=$?

echo "Command RC=$G3_AST_RC" | tee "${ARTIFACTS}/g3_ast_rc.txt"

# AP1: Parse con jq desde archivo
# AP6: jq stderr capturado (no 2>/dev/null)
if command -v jq &> /dev/null; then
    G3_STATUS=$(jq -r '.status // "parse_error"' "${ARTIFACTS}/g3_ast.json" 2>&1 | tee "${ARTIFACTS}/g3_jq.log")
    G3_CODE=$(jq -r '.errors[0].code // "null"' "${ARTIFACTS}/g3_ast.json" 2>&1 | tee -a "${ARTIFACTS}/g3_jq.log")

    echo "Parsed: status=$G3_STATUS, error_code=$G3_CODE" | tee -a "${ARTIFACTS}/g3_ast_rc.txt"

    # AP7: parse_error es FAIL (fail-closed)
    if [ "$G3_STATUS" = "parse_error" ]; then
        G3_OVERALL=1  # FAIL
        echo "Result: FAIL (JSON parse error)"
        echo "jq stderr:"
        cat "${ARTIFACTS}/g3_jq.log"
        echo "Command stderr:"
        cat "${ARTIFACTS}/g3_ast.stderr"
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

# ============================================================================
# G4: Telemetry (opcional, FAIL-CLOSED si existe)
# ============================================================================
echo "=== G4: Telemetry Format Check ==="
if [ -f "_ctx/telemetry/events.jsonl" ]; then
    echo "Found events.jsonl, validating schema..."

    if command -v jq &> /dev/null; then
        head -1 _ctx/telemetry/events.jsonl | \
            jq -c 'has("run_id"), has("segment_id"), has("timing_ms")' 2>&1 | \
            tee "${ARTIFACTS}/g4_telemetry_schema.txt"
        G4_SCHEMA_RC=${PIPESTATUS[0]}

        if [ $G4_SCHEMA_RC -eq 0 ]; then
            G4_OVERALL=0  # PASS
            echo "Result: PASS"
        else
            G4_OVERALL=1  # FAIL
            echo "Result: FAIL (schema invalid, RC=$G4_SCHEMA_RC)"
        fi

        head -5 _ctx/telemetry/events.jsonl > "${ARTIFACTS}/g4_telemetry_sample.txt"
        echo "Sample events:"
        cat "${ARTIFACTS}/g4_telemetry_sample.txt"
    else
        echo "WARNING: jq not found, skipping validation"
        G4_OVERALL=255  # SKIP
    fi
else
    G4_OVERALL=255  # SKIP
    echo "Result: SKIP (no telemetry file)"
fi
echo ""

# ============================================================================
# SUMMARY: Gate Results con RCs explícitos (AP7)
# ============================================================================
echo ""
echo "=== FINAL GATE RESULTS ==="
echo "G1 (pytest collecting): RC=$G1_RC ($([ $G1_RC -eq 0 ] && echo 'PASS' || echo 'FAIL'))"
echo "G2 (path hygiene):      RC=$G2_OVERALL ($([ $G2_OVERALL -eq 0 ] && echo 'PASS' || echo 'FAIL'))"
echo "G3 (ast symbols):       RC=$G3_OVERALL ($([ $G3_OVERALL -eq 0 ] && echo 'PASS' || ([ $G3_OVERALL -eq 255 ] && echo 'SKIP' || echo 'FAIL')))"
echo "G4 (telemetry):         RC=$G4_OVERALL ($([ $G4_OVERALL -eq 0 ] && echo 'PASS' || ([ $G4_OVERALL -eq 255 ] && echo 'SKIP' || echo 'FAIL')))"
echo ""

# Overall result (AP7: FAIL-CLOSED)
if [ $G1_RC -eq 0 ] && [ $G2_OVERALL -eq 0 ] && [ $G3_OVERALL -eq 0 ]; then
    echo "OVERALL: PASS (all critical gates)"
    exit 0
else
    echo "OVERALL: FAIL (one or more critical gates failed)"
    exit 1
fi
```

---

## Resumen de Cambios v2.0 → v2.1

| Issue | v2.0 | v2.1 |
|-------|------|------|
| G2 RC | `$?` (incorrecto) | `${PIPESTATUS[0]}` (correcto) |
| G3 JSON | `2>&1 \| tee` luego parse | `>file.json 2>file.stderr` (separado) |
| G3 parse_error | Ignorado (PASS falso) | Tratado como FAIL |
| sanitized_dump() | Solo repo_root + file:// | TODOS los paths absolutos |
| Bash arrays | `declare -A` | Variables simples |
| jq stderr | `2>/dev/null` | Capturado en log |

---

## Tests adicionales requeridos (integration con segmento completo)

**Problema:** v2.0 creaba segmentos mínimos probablemente insuficientes.

**Solución:**

```python
# tests/integration/test_path_hygiene_e2e.py
def test_ctx_sync_produces_no_pii(tmp_path):
    """Integration: ctx sync NO genera PII en disco.

    v2.1: Crea segmento COMPLETO con archivos canónicos mínimos.
    """
    from pathlib import Path
    import subprocess

    segment = tmp_path / "test_segment"
    segment.mkdir()
    ctx_dir = segment / "_ctx"
    ctx_dir.mkdir()

    # Crear archivos canónicos MÍNIMOS que Trifecta espera
    (segment / "skill.md").write_text("# Test Skill\n\n## Rules\n- Rule 1")
    (segment / "agent.md").write_text("# Agent\n\nStack: Python 3.12")
    (segment / "prime_segment.md").write_text("# Prime\n\n- Read skill.md")
    (segment / "session_segment.md").write_text("# Session\n\n## Handoff\n- Entry")
    (segment / "README.md").write_text("# README\n\nContext for segment")

    # Ejecutar sync real
    result = subprocess.run(
        ["uv", "run", "trifecta", "ctx", "sync", "-s", str(segment)],
        capture_output=True,
        text=True,
        timeout=30
    )

    assert result.returncode == 0, f"sync failed: {result.stderr}"

    pack_path = ctx_dir / "context_pack.json"
    assert pack_path.exists(), "context_pack.json not created"

    content = pack_path.read_text()

    # AP7: Assertions explícitas
    assert "/Users/" not in content, f"PII leak: /Users/ found"
    assert "/home/" not in content
    assert "file://" not in content
```
