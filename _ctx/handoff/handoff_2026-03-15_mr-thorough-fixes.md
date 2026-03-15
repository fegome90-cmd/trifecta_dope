# Handoff: mr-thorough Fixes Complete

**Fecha**: 2026-03-15 08:44
**Sesión**: Multi-Agent Thorough Review (mr-thorough)

---

## Resumen Ejecutivo

Se completaron **6 de 7 fixes** planificados. El plan original incluyó:
- 4 fixes de mis cambios recientes (worktree path resolution)
- 3 fixes de issues pre-existentes

**Estado final**: 6 fixes completados, 1 issue pre-existente pendiente (no relacionado con mis cambios).

---

## Fixes Completados

### 1. CRITICAL: RefreshPrimeUseCase (use_cases.py:148)
**Problema**: `execute()` pasaba `repo_root` a `scan_docs()` pero el parámetro ahora se ignora.

**Fix**:
```python
# Antes:
docs = self.file_system.scan_docs(scan_path, repo_root)

# Después:
docs = self.file_system.scan_docs(scan_path, scan_path)
```

**Verificación**: `tests/integration/test_worktree_prime_resolution.py` - 5/5 PASSED

---

### 2. unwrap() Violation (skill_contracts.py:131)
**Problema**: Uso de `.unwrap_err()` viola disciplina de código.

**Fix**: Pattern matching con `match`:
```python
match inp_result:
    case Err(inp_errs):
        for inp_err in inp_errs:
            errors.append(...)
    case Ok(_):
        pass
```

**Verificación**: `test_no_unwrap_in_src` - PASSED

---

### 3. unwrap() Violation (skill_lint_use_case.py:82)
**Problema**: Mismo issue de `.unwrap_err()`.

**Fix**: Pattern matching con imports de `Err, Ok`:
```python
from src.domain.result import Err, Ok

match validation:
    case Err(errs):
        results.append(SkillLintResult(..., errors=errs))
    case Ok(_):
        pass
```

**Verificación**: `test_no_unwrap_in_src` - PASSED

---

### 4. Dead Code (cli.py:1914)
**Problema**: `repo_root` calculado pero no usado significativamente.

**Fix**: Simplificación:
```python
# Antes:
repo_root = path.parent if path.parent != path else path
scan_path = path
use_case.execute(path, scan_path, repo_root)

# Después:
use_case.execute(path, path, path)
```

---

### 5. Parameter Mismatch (test_ctx_wo_gc.py)
**Problema**: Tests usaban `force_dirty=False` pero implementación usa `force=False`.

**Fix**: Reemplazo global de `force_dirty=False` → `force=False` (4 ocurrencias).

**Verificación**: `tests/unit/test_ctx_wo_gc.py` - 18/19 PASSED (1 skipped as integration)

---

### 6. TTL Default Mismatch (helpers.py:431)
**Problema**: Default era 3600 (1h) pero test esperaba 86400 (24h).

**Fix**:
1. Cambiado default a 86400
2. Agregado soporte para env var `WO_LOCK_TTL_SEC`
3. Actualizado `scripts/constants.py`

```python
def check_lock_age(lock_path: Path, max_age_seconds: int | None = None) -> bool:
    if max_age_seconds is None:
        env_ttl = os.environ.get("WO_LOCK_TTL_SEC", "86400")
        try:
            max_age_seconds = int(env_ttl)
        except ValueError:
            max_age_seconds = 86400
```

**Verificación**: `tests/unit/test_helpers_lock_ttl.py` - 3/3 PASSED

---

## Issue Pre-Existente Pendiente

### test_ctx_build_and_sync_use_config_segment_id_ssot

**Ubicación**: `tests/unit/test_cli_fp_gate.py:104-132`

**Error**:
```
❌ Validation Failed
   - Source file listed in pack but missing from disk: prime_cfg-name.md
   - Source file listed in pack but missing from disk: agent_cfg-name.md
   - Source file listed in pack but missing from disk: session_cfg-name.md
```

**Root Cause (Hipótesis)**:
`ValidateContextPackUseCase` construye paths de validación incorrectamente cuando el `segment_id` del config difiere del nombre del directorio.

**Setup del Test**:
- Directorio: `dir_name`
- Config segment: `cfg-name`
- Archivos creados: `agent_cfg-name.md`, `prime_cfg-name.md`, `session_cfg-name.md`

**Archivos a Investigar**:
- `src/application/use_cases.py:677-778` - ValidateContextPackUseCase
- `tests/unit/test_cli_fp_gate.py:104-132` - El test

**Comando de Verificación**:
```bash
uv run pytest tests/unit/test_cli_fp_gate.py::TestCLIFPGate::test_ctx_build_and_sync_use_config_segment_id_ssot -v
```

**Restricciones**:
- NO modificar el test - el comportamiento esperado es correcto
- El fix debe estar en el código de producción

---

## Archivos Modificados

| Archivo | Cambio |
|---------|--------|
| `src/application/use_cases.py` | Fix RefreshPrimeUseCase.scan_docs call |
| `src/domain/skill_contracts.py` | Pattern matching en vez de unwrap_err |
| `src/application/skill_lint_use_case.py` | Pattern matching + imports |
| `src/infrastructure/cli.py` | Simplificación de path handling |
| `tests/unit/test_ctx_wo_gc.py` | force_dirty → force |
| `scripts/helpers.py` | TTL default + env var support |
| `scripts/constants.py` | DEFAULT_LOCK_TTL = 86400 |

---

## Verificación Final

```bash
# Tests específicos de fixes
uv run pytest tests/unit/test_codebase_discipline.py::test_no_unwrap_in_src \
             tests/unit/test_ctx_wo_gc.py \
             tests/unit/test_helpers_lock_ttl.py \
             tests/integration/test_worktree_prime_resolution.py -v

# Resultado: 27 passed, 1 skipped

# Gate completo
make gate-all

# Resultado: 1 failure (pre-existente, no relacionado con estos fixes)
```

---

## Para el Siguiente Agente

**Prompt sugerido**:
```
Investigar y fixear el test pre-existente test_ctx_build_and_sync_use_config_segment_id_ssot.

El problema está en ValidateContextPackUseCase (use_cases.py:677-778) que no resuelve
correctamente los paths de source files cuando el segment_id del config difiere del
nombre del directorio.

Setup: dir_name/ con config segment="cfg-name" y archivos agent_cfg-name.md, etc.
Error: ValidateContextPackUseCase busca archivos con nombre incorrecto.

Restricciones:
- NO modificar el test
- Fix debe estar en producción
- make gate-all debe quedar en verde
```

---

**Checkpoint**: `_ctx/checkpoints/2026-03-15/checkpoint_084436_mr-thorough-fixes-complete.md`
**Bundle**: `~/.pi/agent/bundles/mr-thorough-fixes.json`
