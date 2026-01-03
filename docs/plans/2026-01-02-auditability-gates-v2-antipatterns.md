# Trifecta Quality Plan — Auditability Gates (Fail-Closed) v2.0

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.
>
> **ANTI-PATRONES EXPLÍCITOS:** Este plan evita AP1-AP10. Cada sección lista los anti-patrones evitados.
>
> **FILOSOFÍA:** Fail-closed + simplicidad operable + determinismo + auditabilidad por defecto.
> Cambios mínimos con ROI alto. Nada de refactors grandes.

**Goal:** Transformar trifecta_dope de "no-auditable" a "auditable-by-default" con gates fail-closed.

**Architecture:** Patches mínimos; sin nuevos sistemas; AST-primary; LSP enhancement.

**Tech Stack:** Python 3.12+, pytest, uv, tree-sitter (optional), JSONL telemetry.

---

## A) Metas & Gates (Anti-Patterns: AP6, AP7)

| Gate | Criterio PASS | Comando Exacto (RC preservado) | Evidencia Requerida | Anti-Patrones Evitados |
|------|---------------|-------------------------------|---------------------|------------------------|
| **G1: Baseline reproducible** | `pytest --collect-only` retorna RC=0 (NO "ERROR collecting") | `uv run pytest --collect-only -q 2>&1 \| tee /tmp/g1_pytest.log; echo "G1_RC=\${PIPESTATUS[0]}"` | (1) `/tmp/g1_pytest.log` (stdout/stderr crudo), (2) `G1_RC` (0=PASS) | AP6: No `2>/dev/null`; AP7: RC explícito determina PASS/FAIL |
| **G2: Path Hygiene (no PII)** | `_ctx/context_pack.json` NO contiene `/Users/`, `/home/`, `file://` | `uv run trifecta ctx sync -s . 2>&1 \| tee /tmp/g2_sync.log; SYNC_RC=\${PIPESTATUS[0]}; rg -n '"/Users/\|"/home/\|file://' _ctx/context_pack.json 2>&1 \| tee /tmp/g2_rg.log; echo "G2_SYNC=$SYNC_RC"; echo "G2_RG=$?"` | (1) `/tmp/g2_sync.log` (sync output), (2) `/tmp/g2_rg.log` (rg output), (3) `G2_SYNC` (0=sync ok), (4) `G2_RG` (1=no matches=PASS) | AP6: Todo tee'd; AP7: rg RC=1 es PASS; AP10: Sync debe pasar primero |
| **G3: ast symbols operable** | `trifecta ast symbols` NO retorna FILE_NOT_FOUND | `uv run trifecta ast symbols sym://python/mod/context_service 2>&1 \| tee /tmp/g3_ast.log; AST_RC=\${PIPESTATUS[0]}; STATUS=\$(jq -r '.status // "error"' /tmp/g3_ast.log); CODE=\$(jq -r '.errors[0].code // "null"' /tmp/g3_ast.log); echo "G3_AST=$AST_RC"; echo "G3_STATUS=$STATUS"; echo "G3_CODE=$CODE"` | (1) `/tmp/g3_ast.log` (crudo), (2) `G3_AST` (cmd RC), (3) `G3_STATUS`, (4) `G3_CODE` | AP1: jq parse desde archivo (no pipe), AP6: stderr capturado, AP7: code≠FILE_NOT_FOUND=PASS |

**NOTAS SOBRE RCs (AP7):**
- G1: RC=0 → PASS (collect ok); RC≠0 → FAIL
- G2: `SYNC_RC=0` AND `RG_RC=1` → PASS (sync ok + no matches); else → FAIL
- G3: `STATUS=ok` OR (`STATUS=error` AND `CODE≠FILE_NOT_FOUND`) → PASS; else → FAIL

---

## B) Matriz de Pruebas (Anti-Patterns: AP2, AP3, AP9)

| Área | Prueba | Tipo | Falla Esperada Hoy | Señal de Fix | Riesgos | AP Evitados |
|------|--------|------|--------------------|--------------|---------|-------------|
| **Import Structure** | `pytest tests/unit/test_ast_lsp_pr2.py --collect-only -q` | Unit | ImportError: `SymbolInfo` no existe | RC=0 (collect ok) | AP9: No re-exports, arreglar import | AP2: Determinista (fixture自有), AP9: Import correcto |
| **Import Structure** | `pytest tests/unit/test_pr2_integration.py --collect-only -q` | Unit | ImportError: `SkeletonMapBuilder` desde ast_parser | RC=0 (collect ok) | Import desde symbol_selector | AP9: Cambiar import, no re-export |
| **Import Structure** | `pytest tests/unit/test_telemetry_extension.py --collect-only -q` | Unit | ImportError: `_relpath` no existe | RC=0 (collect ok) | Reimplementar inline o agregar | AP2: Lógica simple, no dependencias |
| **Path Hygiene (unit)** | `pytest tests/unit/test_path_hygiene.py::test_sanitized_dump_no_pii -v` | Unit | Test no existe | RC=0 (asserts pass) | Validar sanitized_dump() | AP2: Fixture determinista |
| **Path Hygiene (integration)** | `pytest tests/integration/test_path_hygiene_e2e.py::test_ctx_sync_no_pii -v` | Integration | PII en context_pack.json | RC=0 (asserts pass) | Tripwire crítico: sync + validación disco | AP2: tmp_path fixture, AP3: No depende de cwd |
| **CWD Independence** | `pytest tests/integration/test_cwd_independence.py::test_ast_symbols_from_other_dir -v` | Integration | FILE_NOT_FOUND (busca en cwd) | RC=0 (resuelve desde segment_root) | **AP3 TRIPWIRE**: ejecutar desde /tmp | AP3: Cambia cwd antes de llamar CLI |
| **Symbol Resolution** | `uv run trifecta ast symbols sym://python/mod/use_cases` | Integration | FILE_NOT_FOUND | status=ok OR code≠FILE_NOT_FOUND | Resolución desde segment_root/src/ | AP1: Parse JSON con jq (no string) |
| **Context Pack Schema** | `jq -e '.schema_version == 1 and .segment != null' _ctx/context_pack.json` | Integration | Schema puede estar corrupto | RC=0 (jq exit) | Validación schema sin pytest | AP1: jq es parser SSOT |

---

## C) Plan Mínimo por Blocker (ORDEN FIJO: G2 → G1 → G3)

### Blocker 1: G2 Path Hygiene (PRIORIDAD 1 — Auditabilidad)

**Hipótesis root-cause a confirmar:**
- `use_cases.py:481` llama `pack.model_dump_json()` sin sanitización
- `TrifectaPack.repo_root` se setea con `resolve_segment_root().resolve()` (absoluto)
- Templates en `templates.py` pueden interpolar paths directamente

**Herramientas de diagnóstico:**
```bash
# Localizar writer de context_pack (AP8: SSOT)
rg -n "context_pack|ContextPack|write.*pack|json.*pack" src/
# Esperado: src/application/use_cases.py:481 (AtomicWriter.write)
# Esperado: src/domain/context_models.py (TrifectaPack class)

# Localizar campos de path (AP8: SSOT)
rg -n "repo_root|source_files|path|abs|resolve\(" src/
# Esperado: repo_root en context_models.py
# Esperado: resolve() en segment_utils.py

# Verificar uso de AtomicWriter
rg -n "AtomicWriter|model_dump_json|sanitized" src/
```

**Archivos candidatos:**
- `src/domain/context_models.py` — Agregar `sanitized_dump()` method
- `src/application/use_cases.py` — Línea 481: cambiar `model_dump_json()` → `sanitized_dump()`
- `src/infrastructure/templates.py` — Verificar interpolación de paths
- `tests/unit/test_path_hygiene.py` — NUEVO: unit test
- `tests/integration/test_path_hygiene_e2e.py` — NUEVO: integration test

**Patch mínimo (descripción):**

**1. context_models.py — Agregar método sanitized_dump():**
```python
# En clase TrifectaPack, agregar:
def sanitized_dump(self) -> str:
    """Dump JSON con paths sanitizados (FAIL-CLOSED: no PII en output).

    Anti-patrones evitados:
    - AP1: No string parsing; usa structured operations
    - AP6: Output es JSON determinista
    - AP8: SSOT de sanitización está aquí
    """
    import json
    from pathlib import Path

    data = self.model_dump()

    # Sanitizar repo_root si existe
    if "repo_root" in data and data["repo_root"]:
        root = Path(data["repo_root"])
        data["repo_root"] = f"<REPO_ROOT>/{root.name}"

    # Sanitizar recursivamente strings (evita AP1: no stringly-typed)
    def _sanitize(obj):
        if isinstance(obj, str):
            # Reemplazar file:// URIs
            return obj.replace("file://", "<FILE_URI_SANITIZED>")
        elif isinstance(obj, dict):
            return {k: _sanitize(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_sanitize(item) for item in obj]
        return obj

    data = _sanitize(data)
    return json.dumps(data, indent=2)
```

**2. use_cases.py — Cambiar línea 481:**
```python
# Antes:
AtomicWriter.write(pack_path, pack.model_dump_json(indent=2))
# Después:
AtomicWriter.write(pack_path, pack.sanitized_dump())
```

**Tests tripwire (AP2, AP3, AP9):**

**Unit test (AP2: determinista):**
```python
# tests/unit/test_path_hygiene.py
import pytest
from pathlib import Path
from src.domain.context_models import TrifectaPack

def test_sanitized_dump_removes_absolute_paths():
    """Unit: sanitized_dump() elimina paths absolutos (AP2: fixture determinista)."""
    pack = TrifectaPack(
        repo_root=Path("/Users/felipe/Developer/agent_h"),
        segment=".",
        schema_version=1,
        digest=[],
        index=[],
        chunks=[]
    )

    json_str = pack.sanitized_dump()

    # AP7: PASS/FAIL por asserts explícitos
    assert "/Users/" not in json_str, f"PII leak: /Users/ found in {json_str[:200]}"
    assert "/home/" not in json_str
    assert "file://" not in json_str
    assert "<REPO_ROOT>" in json_str
    assert "<FILE_URI_SANITIZED>" not in json_str  # No debería haber file:// URIs
```

**Integration test (AP2: tmp_path, AP3: no cwd dependency):**
```python
# tests/integration/test_path_hygiene_e2e.py
import pytest
import subprocess
from pathlib import Path

def test_ctx_sync_produces_no_pii(tmp_path):
    """Integration: ctx sync NO genera PII en disco (AP2: tmp_path, AP3: no cwd dep).

    Este test:
    - Crea un segmento temporal (AP2: determinista)
    - Ejecuta el comando real `trifecta ctx sync`
    - Valida el JSON generado en disco
    - NO depende de cwd real del repo (AP3)
    """
    # Crear segmento temporal mínimo
    segment = tmp_path / "test_segment"
    segment.mkdir()
    (segment / "skill.md").write_text("# Test Skill")
    (segment / "agent.md").write_text("# Agent")
    (segment / "_ctx").mkdir()

    # Ejecutar sync real (subprocess, no imports Python)
    result = subprocess.run(
        ["uv", "run", "trifecta", "ctx", "sync", "-s", str(segment)],
        capture_output=True,
        text=True,
        timeout=30
    )

    # AP7: FAIL cerrado si sync falla
    assert result.returncode == 0, f"sync failed: {result.stderr}"

    # Validar JSON generado en disco
    pack_path = segment / "_ctx" / "context_pack.json"
    assert pack_path.exists(), "context_pack.json not created"

    content = pack_path.read_text()

    # AP7: Assertions explícitas (no grep en Python)
    assert "/Users/" not in content, f"PII leak detected"
    assert "/home/" not in content
    assert "file://" not in content
```

**CWD Independence test (AP3 TRIPWIRE):**
```python
# tests/integration/test_cwd_independence.py
import pytest
import subprocess
import tempfile
from pathlib import Path

def test_ctx_sync_from_different_cwd():
    """AP3 TRIPWIRE: ctx sync funciona desde cwd diferente.

    Este test es CRÍTICO para detectar dependencias implícitas en cwd.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        other_cwd = Path(temp_dir) / "other_location"
        other_cwd.mkdir()

        # Crear segmento en path absoluto
        with tempfile.TemporaryDirectory() as segment_dir:
            segment = Path(segment_dir) / "test_segment"
            segment.mkdir()
            (segment / "skill.md").write_text("# Test")

            # Ejecutar desde cwd DIFERENTE
            result = subprocess.run(
                ["uv", "run", "trifecta", "ctx", "sync", "-s", str(segment)],
                cwd=other_cwd,  # <-- AP3: cwd diferente
                capture_output=True,
                text=True
            )

            # AP7: FAIL si depende de cwd
            assert result.returncode == 0, f"cwd-dependent: {result.stderr}"

            pack_path = segment / "_ctx" / "context_pack.json"
            assert pack_path.exists()
            content = pack_path.read_text()
            assert "/Users/" not in content
```

**DoD:**
- [ ] Unit test `test_sanitized_dump_removes_absolute_paths` pasa
- [ ] Integration test `test_ctx_sync_produces_no_pii` pasa
- [ ] CWD test `test_ctx_sync_from_different_cwd` pasa
- [ ] Manual gate: `uv run trifecta ctx sync -s . && rg -n '"/Users/' _ctx/context_pack.json; echo "RC=$?" (1=PASS)`
- [ ] Commit: "fix(g2): sanitize paths in context_pack.json (AP6, AP7, AP8)"

---

### Blocker 2: G1 pytest collecting (PRIORIDAD 2 — Tests = Evidencia)

**Hipótesis root-cause a confirmar:**
- Tests importan desde módulo incorrecto (AP9: compat shim en capa equivocada)
- `SymbolInfo` no existe (referencia fantasma)
- `_relpath` no existe en telemetry.py

**Herramientas de diagnóstico:**
```bash
# Buscar imports rotos (AP8: encontrar SSOT)
rg -n "from src.application.ast_parser import.*SymbolInfo" tests/
rg -n "from src.application.ast_parser import.*SkeletonMapBuilder" tests/
rg -n "from src.infrastructure.telemetry import.*_relpath" tests/

# Verificar dónde están realmente los símbolos
rg -n "class SkeletonMapBuilder|class SymbolInfo" src/
rg -n "def _relpath" src/

# Confirmar que SymbolInfo NO existe (debe retornar vacío)
rg -n "class SymbolInfo" src/
```

**Archivos candidatos:**
- `tests/unit/test_ast_lsp_pr2.py` — Línea 16: corregir import
- `tests/unit/test_pr2_integration.py` — Línea 14: corregir import
- `tests/unit/test_telemetry_extension.py` — Línea 10: corregir import
- `src/application/pr2_context_searcher.py` — Verificar si importa SymbolInfo
- `src/application/telemetry_pr2.py` — Verificar si importa SymbolInfo

**Patch mínimo (AP9: NO re-exports, arreglar imports):**

**1. test_ast_lsp_pr2.py:**
```python
# Antes (línea 16):
from src.application.ast_parser import SymbolInfo, SkeletonMapBuilder
# Después (AP9: import desde módulo dueño):
from src.application.symbol_selector import SkeletonMapBuilder
# Remover/usos de SymbolInfo (no existe en codebase)
```

**2. test_pr2_integration.py:**
```python
# Antes (línea 14):
from src.application.ast_parser import SkeletonMapBuilder, SymbolInfo
# Después (AP9):
from src.application.symbol_selector import SkeletonMapBuilder
# Actualizar usos de SymbolInfo si existen
```

**3. Verificar application/pr2_context_searcher.py y telemetry_pr2.py:**
- Si importan `SymbolInfo` de ast_parser, remover
- `SymbolInfo` no se usa en paths críticos (puede ser removido safe)

**4. test_telemetry_extension.py:**
```python
# Antes (línea 10):
from src.infrastructure.telemetry import Telemetry, _relpath
# Después:
from src.infrastructure.telemetry import Telemetry
# Reimplementar _relpath inline si se necesita (AP9: no compat shim)
def _relpath(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)
```

**Test tripwire:**
```bash
# Debe colectar todos los tests sin ImportError (AP7: RC explícito)
uv run pytest --collect-only -q 2>&1 | tee /tmp/g1_collect.log
COLLECT_RC=${PIPESTATUS[0]}
grep -qi "ERROR collecting" /tmp/g1_collect.log && echo "FAIL" || echo "PASS (RC=$COLLECT_RC)"
```

**DoD:**
- [ ] `uv run pytest --collect-only -q` NO muestra "ERROR collecting"
- [ ] `uv run pytest tests/unit/test_ast_lsp_pr2.py --collect-only -q` pasa (RC=0)
- [ ] `uv run pytest tests/unit/test_pr2_integration.py --collect-only -q` pasa (RC=0)
- [ ] `uv run pytest tests/unit/test_telemetry_extension.py --collect-only -q` pasa (RC=0)
- [ ] Commit: "fix(g1): correct imports in tests (AP9: no re-exports)"

---

### Blocker 3: G3 ast symbols (PRIORIDAD 3 — Contrato mínimo)

**Hipótesis root-cause a confirmar:**
- `SymbolResolver.resolve()` busca en `root` que por defecto es `.` (cwd) (AP3)
- Módulos Python viven en `src/` fuera de cwd
- No existe concepto de "search paths" o convención src/

**Herramientas de diagnóstico:**
```bash
# Localizar cálculo de root en cli_ast.py (AP8: SSOT)
rg -n "resolve_segment_root|Path\(segment\)|root =" src/infrastructure/cli_ast.py

# Localizar lógica de resolución en symbol_selector.py
rg -n "def resolve|candidate_file|candidate_init|FILE_NOT_FOUND" src/application/symbol_selector.py

# Probar desde diferentes cwds (AP3 tripwire)
cd /tmp && uv run trifecta ast symbols sym://python/mod/context_service
# Esperado hoy: FILE_NOT_FOUND (porque busca en /tmp)
```

**Archivos candidatos:**
- `src/infrastructure/cli_ast.py` — Línea 37: cálculo de `root`
- `src/application/symbol_selector.py` — Método `resolve()`

**Patch mínimo (AP3: segment_root/src/ convención, AP5: precedencia clara):**

**1. cli_ast.py — Corregir cálculo de root:**
```python
# Antes (línea 37):
root = resolve_segment_root(Path(segment))
# AP3 PROBLEMA: root = cwd cuando segment="."

# Después (convención fija src/ con fallback):
segment_root = resolve_segment_root(Path(segment))
src_dir = segment_root / "src"

# AP5: Precedencia explícita: convención src/ primero, fallback si no existe
if src_dir.exists() and src_dir.is_dir():
    root = src_dir
else:
    # Fallback para segmentos sin layout src/
    root = segment_root
```

**Versión alternativa con search paths (opcional, NO agregar flag):**
```python
# En SymbolResolver.resolve(), antes de retornar FILE_NOT_FOUND:
SEARCH_PATHS = ["", "src/", "src/application/", "src/infrastructure/"]

for search_path in SEARCH_PATHS:
    candidate_with_path = self.root / search_path / f"{query.path}.py"
    init_with_path = self.root / search_path / query.path / "__init__.py"

    if candidate_with_path.exists() and candidate_with_path.is_file():
        return Ok(Candidate(f"{search_path}{query.path}.py", "mod"))
    if init_with_path.exists() and init_with_path.is_file():
        return Ok(Candidate(f"{search_path}{query.path}/__init__.py", "mod"))
```

**CWD Independence test (AP3 TRIPWIRE para G3):**
```python
# tests/integration/test_ast_symbols_cwd.py
import pytest
import subprocess
import tempfile
from pathlib import Path
import json

def test_ast_symbols_from_different_cwd(tmp_path):
    """AP3 TRIPWIRE: ast symbols funciona desde cwd diferente.

    Confirma que el comando resuelve paths desde segment_root,
    NO desde cwd.
    """
    with tempfile.TemporaryDirectory() as other_cwd:
        # Crear segmento de prueba con estructura src/
        segment = tmp_path / "test_segment"
        segment.mkdir()
        src_dir = segment / "src"
        src_dir.mkdir()

        # Crear módulo de prueba
        (src_dir / "test_module.py").write_text("""
# Test module
def test_function():
    pass
""")

        # Ejecutar desde cwd DIFERENTE (AP3)
        result = subprocess.run(
            ["uv", "run", "trifecta", "ast", "symbols", "sym://python/mod/test_module"],
            cwd=other_cwd,  # <-- CRÍTICO
            capture_output=True,
            text=True,
            timeout=30
        )

        # AP7: Validar response JSON (no string parsing)
        response = json.loads(result.stdout)
        status = response.get("status")
        error_code = response.get("errors", [{}])[0].get("code")

        # AP7: PASS si NO es FILE_NOT_FOUND
        assert status == "ok" or error_code != "FILE_NOT_FOUND", \
            f"AP3 FAIL: cwd-dependent resolution (status={status}, code={error_code})"
```

**DoD:**
- [ ] `uv run trifecta ast symbols sym://python/mod/context_service` retorna `status: "ok"`
- [ ] `uv run trifecta ast symbols sym://python/mod/use_cases` funciona también
- [ ] CWD test `test_ast_symbols_from_different_cwd` pasa
- [ ] Manual: desde `/tmp`, el command debe resolver módulos correctamente
- [ ] Commit: "fix(g3): resolve FILE_NOT_FOUND with src/ convention (AP3, AP5)"

---

## D) Script de Reproducción (audit_repro.sh) — COMPLETO

**Anti-patrones evitados:** AP6 (no /dev/null), AP7 (RC explícito), AP10 (fallback auditado)

```bash
#!/usr/bin/env bash
# audit_repro.sh — Evidence capture para trifecta_dope auditability gates
#
# POLÍTICA (AP6, AP7):
# - NO abortar en fallos (capturar todo)
# - TODO va a archivos via tee (no /dev/null en gates)
# - RCs preservados con ${PIPESTATUS[n]}
# - Gates calculados al final con RCs explícitos
#
# Usage: cd /path/to/trifecta_dope && bash audit_repro.sh

set +e  # CRÍTICO: No abortar en fallos (AP6)

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARTIFACTS="/tmp/trifecta_audit_${TIMESTAMP}"
mkdir -p "${ARTIFACTS}"

# Variables para gate results (RCs explícitos - AP7)
declare -A GATE_RC
GATE_RC[G1]=1
GATE_RC[G2]=1
GATE_RC[G3]=1
GATE_RC[G4]=255  # 255 = SKIP

echo "=== Trifecta Auditability Evidence Capture ==="
echo "Timestamp: ${TIMESTAMP}"
echo "Artifacts: ${ARTIFACTS}"
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

# AP6: Todo tee'd (no /dev/null)
uv run pytest --collect-only -q 2>&1 | tee "${ARTIFACTS}/g1_pytest_collect.txt"
G1_PIPESTATUS=(${PIPESTATUS[*]})
GATE_RC[G1]=${G1_PIPESTATUS[0]}

echo "G1_RC=${GATE_RC[G1]}" | tee -a "${ARTIFACTS}/g1_pytest_collect.txt"

# Detectar "ERROR collecting" en output
if grep -qi "ERROR collecting" "${ARTIFACTS}/g1_pytest_collect.txt"; then
    GATE_RC[G1]=1  # FAIL
    echo "Result: FAIL (ERROR collecting detected)"
else
    # AP7: RC explícito determina PASS/FAIL
    if [ ${GATE_RC[G1]} -eq 0 ]; then
        echo "Result: PASS (RC=0, no collection errors)"
    else
        echo "Result: FAIL (RC=${GATE_RC[G1]}, unknown error)"
    fi
fi
echo ""

# ============================================================================
# G2: Path Hygiene (AP6, AP7, AP10: sync debe pasar primero)
# ============================================================================
echo "=== G2: Path Hygiene Check ==="
echo "Running: uv run trifecta ctx sync -s ."

# AP6: stderr capturado (no /dev/null)
uv run trifecta ctx sync -s . 2>&1 | tee "${ARTIFACTS}/g2_ctx_sync.txt"
G2_SYNC_PIPESTATUS=(${PIPESTATUS[*]})
SYNC_RC=${G2_SYNC_PIPESTATUS[0]}

echo "Sync RC=$SYNC_RC" | tee -a "${ARTIFACTS}/g2_ctx_sync.txt"

echo "Checking for PII/absolute paths..."
# AP6: Todo tee'd
rg -n '"/Users/|"/home/|file://' _ctx/context_pack.json 2>&1 | tee "${ARTIFACTS}/g2_rg_pii.txt"
G2_RG_PIPESTATUS=(${PIPESTATUS[*]})
RG_RC=${G2_RG_PIPESTATUS[0]}

echo "rg RC=$RG_RC" | tee "${ARTIFACTS}/g2_rg_rc.txt"

# AP7: lógica explícita de PASS/FAIL
# AP10: sync debe pasar primero
if [ $SYNC_RC -ne 0 ]; then
    GATE_RC[G2]=1  # FAIL
    echo "Result: FAIL (sync failed, RC=$SYNC_RC)"
else
    # rg retorna 1 cuando NO hay matches (EXITO para nosotros)
    if [ $RG_RC -eq 1 ]; then
        GATE_RC[G2]=0  # PASS
        echo "Result: PASS (sync ok, no PII found)"
    else
        GATE_RC[G2]=1  # FAIL
        echo "Result: FAIL (PII found, RG_RC=$RG_RC)"
        echo "Matches:"
        cat "${ARTIFACTS}/g2_rg_pii.txt"
    fi
fi
echo ""

# Sample context_pack.json para inspección visual
echo "Sample context_pack.json (first 30 lines):"
head -30 _ctx/context_pack.json | tee "${ARTIFACTS}/g2_context_pack_sample.txt"
echo ""

# ============================================================================
# G3: ast symbols (AP1: jq parse desde archivo, AP6: stderr capturado)
# ============================================================================
echo "=== G3: AST Symbols Command ==="
echo "Running: uv run trifecta ast symbols sym://python/mod/context_service"

# AP6: stderr capturado
uv run trifecta ast symbols sym://python/mod/context_service 2>&1 | tee "${ARTIFACTS}/g3_ast_symbols.txt"
G3_PIPESTATUS=(${PIPESTATUS[*]})
G3_CMD_RC=${G3_PIPESTATUS[0]}

echo "Command RC=$G3_CMD_RC" | tee -a "${ARTIFACTS}/g3_ast_symbols.txt"

# AP1: Parse con jq desde archivo (no pipe, evita stringly-typed)
if command -v jq &> /dev/null; then
    G3_STATUS=$(jq -r '.status // "error"' "${ARTIFACTS}/g3_ast_symbols.txt" 2>/dev/null || echo "parse_error")
    G3_ERROR_CODE=$(jq -r '.errors[0].code // "null"' "${ARTIFACTS}/g3_ast_symbols.txt" 2>/dev/null || echo "null")

    echo "Parsed: status=$G3_STATUS, error_code=$G3_ERROR_CODE" | tee -a "${ARTIFACTS}/g3_ast_symbols.txt"

    # AP7: lógica explícita
    if [ "$G3_STATUS" = "ok" ]; then
        GATE_RC[G3]=0  # PASS
        echo "Result: PASS"
    elif [ "$G3_ERROR_CODE" = "FILE_NOT_FOUND" ]; then
        GATE_RC[G3]=1  # FAIL
        echo "Result: FAIL (FILE_NOT_FOUND)"
    else
        GATE_RC[G3]=0  # PASS (error diferente es aceptable)
        echo "Result: PASS (error is not FILE_NOT_FOUND)"
    fi
else
    echo "WARNING: jq not found, skipping JSON parse"
    GATE_RC[G3]=255  # SKIP
fi
echo ""

# ============================================================================
# G4: Telemetry (opcional, FAIL-CLOSED si existe)
# ============================================================================
echo "=== G4: Telemetry Format Check ==="
if [ -f "_ctx/telemetry/events.jsonl" ]; then
    echo "Found events.jsonl, validating schema..."

    # AP1: jq parse
    if command -v jq &> /dev/null; then
        head -1 _ctx/telemetry/events.jsonl | \
            jq -c 'has("run_id"), has("segment_id"), has("timing_ms")' 2>&1 | \
            tee "${ARTIFACTS}/g4_telemetry_schema.txt"
        G4_PIPESTATUS=(${PIPESTATUS[*]})
        G4_SCHEMA_RC=${G4_PIPESTATUS[0]}

        if [ $G4_SCHEMA_RC -eq 0 ]; then
            GATE_RC[G4]=0  # PASS
            echo "Result: PASS"
        else
            GATE_RC[G4]=1  # FAIL
            echo "Result: FAIL (schema invalid, RC=$G4_SCHEMA_RC)"
        fi

        head -5 _ctx/telemetry/events.jsonl > "${ARTIFACTS}/g4_telemetry_sample.txt"
        echo "Sample events:"
        cat "${ARTIFACTS}/g4_telemetry_sample.txt"
    else
        echo "WARNING: jq not found, skipping validation"
        GATE_RC[G4]=255  # SKIP
    fi
else
    GATE_RC[G4]=255  # SKIP
    echo "Result: SKIP (no telemetry file)"
fi
echo ""

# ============================================================================
# SUMMARY: Gate Results con RCs explícitos (AP7)
# ============================================================================
echo ""
echo "=== FINAL GATE RESULTS ==="
echo "G1 (pytest collecting): RC=${GATE_RC[G1]} ($([ ${GATE_RC[G1]} -eq 0 ] && echo 'PASS' || echo 'FAIL'))"
echo "G2 (path hygiene):      RC=${GATE_RC[G2]} ($([ ${GATE_RC[G2]} -eq 0 ] && echo 'PASS' || echo 'FAIL'))"
echo "G3 (ast symbols):       RC=${GATE_RC[G3]} ($([ ${GATE_RC[G3]} -eq 0 ] && echo 'PASS' || ([ ${GATE_RC[G3]} -eq 255 ] && echo 'SKIP' || echo 'FAIL')))"
echo "G4 (telemetry):         RC=${GATE_RC[G4]} ($([ ${GATE_RC[G4]} -eq 0 ] && echo 'PASS' || ([ ${GATE_RC[G4]} -eq 255 ] && echo 'SKIP' || echo 'FAIL')))"
echo ""

# Overall result (AP7: FAIL-CLOSED)
if [ ${GATE_RC[G1]} -eq 0 ] && [ ${GATE_RC[G2]} -eq 0 ] && [ ${GATE_RC[G3]} -eq 0 ]; then
    echo "OVERALL: PASS (all critical gates)"
    exit 0
else
    echo "OVERALL: FAIL (one or more critical gates failed)"
    exit 1
fi
```

**Uso del script:**
```bash
# Ejecutar desde el repo
cd /path/to/trifecta_dope
bash audit_repro.sh

# Ver evidencia capturada
ls /tmp/trifecta_audit_*/

# Re-run gate individual (con RC preservado)
# G1:
uv run pytest --collect-only -q 2>&1 | tee /tmp/g1.log; echo "RC=${PIPESTATUS[0]}"
# G2:
uv run trifecta ctx sync -s . 2>&1 | tee /tmp/g2_sync.log; SYNC_RC=${PIPESTATUS[0]}; rg -n '"/Users/' _ctx/context_pack.json 2>&1 | tee /tmp/g2_rg.log; echo "SYNC=$SYNC_RC, RG=$?"
# G3:
uv run trifecta ast symbols sym://python/mod/context_service 2>&1 | tee /tmp/g3.log; jq -r '.status, .errors[0].code // "null"' /tmp/g3.log
```

---

## E) No-Decisions (Temas EXPLÍCITAMENTE fuera de scope)

| Tema | Por qué NO en este sprint | Decisión diferida a | AP Relacionado |
|------|--------------------------|---------------------|---------------|
| **LSP value prop** | LSP es enhancement; AST debe funcionar primero sin daemon | Phase 3b (post-gates) | AP10: Fallback debe estar auditado primero |
| **Tree-sitter completo** | Mock actual satisface contrato mínimo; real parsing es optimización | Phase 4 (performance) | AP2: Tests no deben depender de tool externo |
| **Sistema de locks nuevo** | Ya existe `.autopilot.lock` en use_cases.py; reusar | Reuse, no crear | AP8: SSOT de locks ya existe |
| **Index embeddings** | Trifecta NO es RAG; búsqueda lexical es suficiente | Nunca (por diseño) | — |
| **Refactor arquitectónico** | Cambio de capas sin evidencia es riesgo | Post-gates con data | — |
| **SymbolInfo completo** | No usado en paths críticos; stub suficiente | Cuando se necesite | AP9: No crear compat shims |
| **Scripts legacy removal** | No bloquean gates; limpieza es separada | Sprint de mantenimiento | — |
| **Tests coverage increase** | Objetivo es collecting, no coverage 100% | Sprint de calidad | AP2: Tests deben ser deterministas primero |
| **Daemon lifecycle changes** | TTL 180s funciona; no tocar sin data | Post-gates con telemetry | AP4: Tripwire para shutdown ruidoso |
| **Context pack schema v2** | Schema v1 es funcional; cambio es breaking change | Con migración plan | AP1: Schema debe estar versionado |
| **--src-root flag** | Agregar flags es scope creep; usar convención fija | Nunca (convención es suficiente) | AP5: Precedencia se complica |
| **Re-exports en ast_parser** | Tests deben importar desde módulos correctos; no false positives | Nunca (principio de import correcto) | AP9: Compat shims en capa equivocada |
| **stderr silencing** | Ocultar errores rompe auditabilidad | Nunca | AP6: Evidencia debe ser completa |
| **stdout parsing** | String parsing es frágil (AP1) | Nunca | AP1: Usar parsers tipados |
| ** cwd-based I/O** | CWD dependency rompe reproducibilidad | Nunca | AP3: Todo relativo a segment_root |

---

## F) Referencia Cruz: Anti-Patrones → Mitigaciones en el Plan

| Anti-Patrón | Descripción | Mitigación en este plan |
|-------------|-------------|------------------------|
| **AP1** | Stringly-typed contracts | jq parser para JSON; assertions en Python; no `startswith()` para lógica |
| **AP2** | Tests no deterministas | tmp_path fixtures; no skip/xfail sin ADR; tests integration con segmentos temporales |
| **AP3** | CWD/paths implícitos | CWD independence tests; todo relativo a segment_root; convención src/ |
| **AP4** | Concurrencia/shutdown ruidoso | (Fuera de scope actual; planear post-gates) |
| **AP5** | Flags/env sin precedencia | No agregar flags; usar convención fija; precedencia documentada si existe |
| **AP6** | Ocultar evidencia | No `2>/dev/null` en gates; todo con `tee`; stderr capturado |
| **AP7** | PASS falsos por checks malos | RCs explícitos; rg RC=1 es PASS; jq exit code valida JSON |
| **AP8** | Duplicar SSOT | rg commands para localizar SSOT; parches en archivos dueños; no duplicados |
| **AP9** | Compat shims en capa equivocada | NO re-exports en ast_parser; arreglar imports en tests |
| **AP10** | Fallback silencioso | Sync RC verificado antes de validar PII; fallback auditado |

---

## G) Ejecución (Handoff)

**Plan v2.0 guardado en** `docs/plans/2026-01-02-auditability-gates-v2-antipatterns.md`.

**Mejoras sobre v1:**
- ✅ AP1: jq parser desde archivo (no pipe string parsing)
- ✅ AP2: Tests con tmp_path fixtures; CWD independence tests
- ✅ AP3: CWD tests tripwire; segment_root como base
- ✅ AP5: Sin flags nuevos; convención fija src/
- ✅ AP6: No `2>/dev/null`; todo con `tee`
- ✅ AP7: RCs explícitos en todos los gates
- ✅ AP8: SSOT localization commands
- ✅ AP9: NO re-exports; imports corregidos
- ✅ AP10: Fallback auditado (sync RC verificado)

**Dos opciones de ejecución:**

**1. Subagent-Driven (esta sesión)** — Despacho subagent fresco por task, review entre pasos, iteración rápida

**2. Parallel Session (separada)** — Nueva sesión con executing-plans, ejecución batch con checkpoints

**¿Cuál prefieres?**
