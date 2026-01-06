# AUDITORÍA "NO-LE-CREO-NADA" (RED TEAM) — FAIL-CLOSED

**Role**: Auditor paranoico + ejecutor reproducible  
**Repo Root**: `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope`  
**Audit Commit**: `ff3374f5a8b02874195c67e18171b87b8d1950b7`  
**Worktree**: `/tmp/tf_audit_ff3374f5a8b02874195c67e18171b87b8d1950b7`  
**Timestamp**: 2026-01-05T19:04:00-03:00

---

## 1. LISTADO DE LOGS GENERADOS

```
-rw-r--r--  255 audit_env.log
drwxr-xr-x 1024 search_dataset_v1/
-rw-r--r--  255 wo0001_ls.log
-rw-r--r--  388 wo0001_metrics_raw.json
-rw-r--r-- 5411 wo0001_run_dataset.log
-rw-r--r--  294 wo0001_sha.log
-rw-r--r--  232 wo0002_ls.log
-rw-r--r--   98 wo0002_pytest_1.log
-rw-r--r--   98 wo0002_pytest_2.log
-rw-r--r--  271 wo0002_sha.log
-rw-r--r--   80 wo0003_ls.log
-rw-r--r--    0 wo0003_no_io_grep.log
-rw-r--r--   98 wo0003_pytest_1.log
-rw-r--r--   98 wo0003_pytest_2.log
-rw-r--r--   93 wo0003_sha.log
-rw-r--r--   98 wo0004_ls.log
-rw-r--r--   98 wo0004_pytest_1.log
-rw-r--r--   98 wo0004_pytest_2.log
-rw-r--r--  140 wo0004_smoke_off.log
-rw-r--r-- 2463 wo0005_acceptance.log
-rw-r--r-- 2967 wo0005_gate_full.log
```

---

## 2. TABLA DE VEREDICTOS

| WO | Veredicto | Evidencia | Notas |
|----|-----------|-----------|-------|
| **WO-0001** | **PASS** | `wo0001_run_dataset.log`, `wo0001_metrics_raw.json` | Dataset ejecutado desde cero. JSON generado con estructura válida (total=30, count=10x3). **PERO** hit_rate=0.0 para todas las clases (sin context_pack.json en worktree limpio). Deliverable técnico cumplido pero métrica vacía. |
| **WO-0002** | **PASS** | `wo0002_pytest_1.log`, `wo0002_pytest_2.log`, `wo0002_sha.log` | Código existe (3240 bytes, hash edf19be18d994b2dd56360f8fe17673199db7885b339487bc652154c5f53001f). Tests x2: 4 passed en 0.01s (reproducible, determinista). |
| **WO-0003** | **PASS** | `wo0003_pytest_1.log`, `wo0003_pytest_2.log`, `wo0003_sha.log`, `wo0003_no_io_grep.log` | Código existe (6081 bytes, hash 4e6d84dbbf79144ccf23abb020c9cfe8f2f5ec0d40d5a360fd14083055ad1d00). Tests x2: 6 passed en 0.03s (reproducible). No I/O detectado (grep empty). |
| **WO-0004** | **PASS** | `wo0004_pytest_1.log`, `wo0004_pytest_2.log` | Test file `test_ctx_search_linter.py` existe (13808 bytes). Tests x2: 5 passed en 0.06s/0.07s (reproducible). **NOTA**: Test `test_ctx_search_linter_ab_controlled.py` NO EXISTE (claim erróneo en WO-0004_job.yaml líneas 27, 33). A/B smoke test FALLÓ por context_pack.json faltante (worktree limpio). Telemetría no verificable sin contexto preexistente. |
| **WO-0005** | **NO-PASS** | `wo0005_acceptance.log`, `wo0005_gate_full.log` | Test `test_e2e_evidence_stop_real_cli` FALLÓ: "AssertionError: No IDs found for query 'ContextService'". Gate completo: 1 failed, 474 passed. **El fix aplicado (query 'ContextService' -> 'context') NO está presente en el código auditado (commit ff3374f).** Test depende de estado externo (context_pack.json del repo principal). |

---

## 3. EXTRACTOS LITERALES DE LOGS

### WO-0001: `_ctx/logs/wo0001_run_dataset.log` (últimas 15 líneas)

```
    "semi": {
      "count": 10,
      "hit_rate": 0.0,
      "avg_hits": 0.0,
      "unique_paths_avg": 0.0
    },
    "guided": {
      "count": 10,
      "hit_rate": 0.0,
      "avg_hits": 0.0,
      "unique_paths_avg": 0.0
    }
  }
}
✅ Done.
```

### WO-0002: `_ctx/logs/wo0002_pytest_1.log`

```
....                                                                     [100%]
4 passed in 0.01s
```

### WO-0003: `_ctx/logs/wo0003_pytest_1.log`

```
......                                                                   [100%]
6 passed in 0.03s
```

### WO-0004: `_ctx/logs/wo0004_pytest_1.log`

```
.....                                                                    [100%]
5 passed in 0.07s
```

### WO-0005: `_ctx/logs/wo0005_gate_full.log` (últimas 15 líneas)

```
            if line.strip() and "[" in line and "]" in line:
                start = line.find("[")
                end = line.find("]")
                if start != -1 and end != -1:
                    ids.append(line[start + 1 : end])
    
>       assert len(ids) > 0, f"No IDs found for query '{query}'"
E       AssertionError: No IDs found for query 'ContextService'
E       assert 0 > 0
E        +  where 0 = len([])

tests/acceptance/test_pd_evidence_stop_e2e.py:110: AssertionError
=========================== short test summary info ============================
FAILED tests/acceptance/test_pd_evidence_stop_real_cli
1 failed, 474 passed, 3 skipped in 12.60s
```

---

## 4. TELEMETRÍA (JSONL)

**Estado**: NO DISPONIBLE

**Razón**: Worktree limpio no tiene `context_pack.json` ni contexto inicializado. CLI falla con:

```
❌ Search Error
   Detail: Context pack not found at /private/tmp/tf_audit_ff3374f5a8b02874195c67e18171b87b8d1950b7/_ctx/context_pack.json
```

Intentos de crear contexto (`trifecta create`, `trifecta ctx build`) fallaron por:

1. Validación `AGENTS.md` faltante
2. Validación de nombres de archivos `_ctx/{prime,agent,session}_segment.md` vs `_ctx/{prime,agent,session}_<dirname>.md` (conflicto de convención)
3. Sin JSONL eventos generados

**Conclusión**: WO-0004 depende críticamente de estado preexistente (context_pack.json, telemetry eventos) que NO se puede reproducir en entorno limpio sin ciclo completo de inicialización.

---

## 5. VEREDICTO FINAL POR WO (SIN DECORATIVOS)

```
WO-0001: PASS (con nota: métrica vacía por worktree limpio)
WO-0002: PASS
WO-0003: PASS
WO-0004: PASS (tests unitarios/integración) | NO-REPRODUCIBLE (A/B smoke, telemetría)
WO-0005: NO-PASS (test falla, fix no aplicado en commit auditado)
```

---

## 6. HALLAZGOS CRÍTICOS

### 6.1. WO-0004: Claim erróneo en `WO-0004_job.yaml`

**Claim (línea 27, 33)**:

```yaml
deliverables:
  - "Integration test A/B controlled (OFF=0, ON>0)"
verify:
  commands:
    - "uv run pytest -q tests/integration/test_ctx_search_linter_ab_controlled.py"
```

**Evidencia**: Archivo `test_ctx_search_linter_ab_controlled.py` **NO EXISTE** en commit `ff3374f`.

**Archivos reales**:

```
tests/integration/test_ctx_search_linter.py (13808 bytes)
tests/unit/test_search_usecase_linter.py
```

**Conclusión**: Deliverable declarado ficticio o renombrado sin actualizar job.yaml.

### 6.2. WO-0005: Regresión confirmada

**Test falla** con query 'ContextService' (línea 240 de `test_pd_evidence_stop_e2e.py`).

**Fix descrito en WO-0005_job.yaml** (líneas 51-53):

```yaml
fix_applied:
  file: "tests/acceptance/test_pd_evidence_stop_e2e.py"
  lines: [240, 259]
  change: "query: 'ContextService' -> 'context'"
```

**Evidencia**: Fix **NO aplicado** en commit auditado. Test FALLA exactamente con 'ContextService'.

**Conclusión**: WO-0005 marcado "done" pero fix no mergeado/committed a HEAD.

### 6.3. Dependencia de estado externo (reproducibilidad rota)

**Problema**: Tests E2E y smoke CLI dependen de:

- `_ctx/context_pack.json` pre-generado
- Contexto inicializado (`prime_*.md`, `agent_*.md`, `session_*.md`)
- Telemetría histórica (`events.jsonl`)

**Impacto**: Auditoría en worktree limpio NO puede validar claims de A/B delta, sanitización JSONL, etc.

**Mitigación necesaria**: Fixtures de test con contexto sintético auto-generado, o gate de "smoke tests requiere contexto pre-existente".

---

## 7. RECOMENDACIONES

1. **WO-0004**: Actualizar `WO-0004_job.yaml` con nombre correcto del archivo de test.
2. **WO-0005**: Aplicar fix (`'ContextService' -> 'context'`) o documentar como pre-existing en `KNOWN_FAILS.md`.
3. **Reproducibilidad**: Crear fixture `tests/fixtures/context_pack_synthetic.json` para habilitar smoke tests sin dependencia de repo state.
4. **Gate hardening**: Pre-commit hook que bloquee merge si `pytest -q` tiene failures (salvo `KNOWN_FAILS.md`).

---

**FIN DE AUDITORÍA**
