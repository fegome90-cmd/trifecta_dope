# ¿Qué van a borrar? - Análisis Fail-Closed

**Fecha**: 2026-01-04  
**Auditor**: Modo Fail-Closed (cero asunciones, solo evidencia)  
**Fuentes Analizadas**:
- `AUDIT_REPORT_FAILCLOSED.md`
- `FINAL_PROPOSAL.md`
- `braindope_session_logging.md`
- Repo actual (via Trifecta CLI + comandos reproducibles)

---

## 1) VEREDICTO: ¿QUÉ VAN A BORRAR?

**Se borra (existente):** **NADA.**

**Evidencia literal**:
> AUDIT_REPORT_FAILCLOSED.md:L20: **verdict**: ✅ **CERO features eliminadas**. Todas son extensiones.

**Confirmaciones via comandos reproducibles**:
```bash
# session_append EXISTE
$ uv run trifecta ast symbols "sym://python/mod/src.infrastructure.cli"
{"symbols": [..., {"kind": "function", "name": "session_append", "line": 1281}]}

# session query NO EXISTE (comando nuevo, no borrado)
$ rg "def.*session.*query" src/ --type py
(exit code 1 - no matches)

# session*.jsonl NO EXISTE (nunca existió, no se borra)
$ ls _ctx/session*.jsonl 2>&1
fish: No matches for wildcard '_ctx/session*.jsonl'

# Telemetry EXISTE y SE MANTIENE
$ ls -la _ctx/telemetry/events.jsonl
-rw-r--r-- 1 felipe_gonzalez staff 606421 Jan 4 12:26 _ctx/telemetry/events.jsonl
```

---

## 2) QUÉ NO SE BORRA (EXISTENTE) PERO SE TOCA

| Feature | Cambio | Riesgo | Gate/Test | Evidencia |
|:--------|:-------|:-------|:----------|:----------|
| **session append** | Se extiende con dual write (telemetry + session.md) | ⚠️ Si solo escribe a telemetry → rompe 3 tests | `pytest tests/unit/test_session_and_normalization.py -v` MUST PASS | AST symbols: `session_append` L1281 (cli.py) |
| **session.md** | Se mantiene como log humano. Puede generarse desde JSONL (V2) | ⚠️ Si deja de actualizarse → historia congelada | Debe seguir siendo escrito en V1 (dual write) | `_ctx/session_trifecta_dope.md` (21KB, 397 líneas) |
| **telement JSONL** | Se añade event type `session.entry` | ✅ Bajo - event type nuevo, no rompe existentes | Verificar schema sanitization | `_ctx/telemetry/events.jsonl` (606KB, 2186 eventos) |

**Evidencia de riesgo session.md**:
> AUDIT:L79-L95: **PREGUNTA CRÍTICA**: ¿El cambio V1 hace que session.md **deje de actualizarse**?  
> AUDIT:L95: **RECOMENDACIÓN**: V1 debe escribir a AMBOS para mantener backward compat total.

**Tests que NO deben romperse** (AUDIT:L196-L200):
1. `test_session_append_creates_file` - Debe seguir creando session.md
2. `test_session_append_appends_second_entry` - Debe seguir appendeando  
3. `test_session_append_includes_pack_sha_when_present` - Debe incluir pack_sha

**Fix obligatorio** (AUDIT:L204-L212):
```python
# V1 debe hacer dual write:
# 1. Write to telemetry (new)
telemetry.event(cmd="session.entry", args={...}, result={...}, timing_ms=0)

# 2. Write to session.md (existing - keep for backward compat)
with open(session_file, "a") as f:
    f.write(entry_text)
```

---

## 3) QUÉ SE DESCARTA (NUNCA EXISTIÓ)

**Estos nunca estuvieron implementados → NO hay borrado, son ideas rechazadas:**

| Feature Propuesta | Estado | Evidencia de NO-EXISTENCIA | Alternativa Adoptada |
|:------------------|:-------|:---------------------------|:---------------------|
| **session_journal.jsonl separado** | Nunca existió | `ls _ctx/session*.jsonl` → No matches (exit 124) | Reutilizar telemetry.jsonl con event type |
| **Auto-detección de tool use** | Nunca existió | `rg "auto.*detect.*tool" src/` → 0 matches (AUDIT:L35-L40) | Flags `--files`, `--commands` (YA EXISTEN) |
| **Background daemon/script** | Nunca existió | `rg "daemon.*session" .` → 0 matches (AUDIT:L42-L47) | Hook síncrono en session append |
| **session query command** | Nunca existió | `rg "def.*session.*query" src/` → exit 1 (no matches) | Comando NUEVO en V1 |
| **session load command** | Nunca existió | `uv run trifecta session load --help` → "No such command 'load'" (exit 2) | Comando NUEVO en V1 |

**Rationale de descarte** (braindope:L391-L400):
> ### 💀 Feature: Auto-detección de Tool Use  
> **Razón de Eliminación**: No es necesaria, metadata es manual (flags existentes)  
> **Ahorro Estimado**: ~15 horas de parser complejo  
> **Alternativa Adoptada**: Flags `--files` y `--commands` (ya existen)
>
> ### 💀 Arquitectura: session_journal.jsonl separado  
> **Razón de Eliminación**: Usuario decidió reutilizar telemetry (no reinventar rueda)  
> **Ahorro Estimado**: ~10 horas (evita JSONL writer duplicado)  
> **Alternativa Adoptada**: Event type `session.entry` en telemetry existente

---

## 4) QUÉ SE "OCULTA" EN OUTPUTS (CLEAN)

**Campos filtrados en `session query --format clean`** (NO es borrado, es limpieza de output):

| Campo | Por qué se oculta | Riesgo de Contrato | Cómo acceder RAW |
|:------|:------------------|:-------------------|:-----------------|
| `run_id` | Irrelevante para session context | BAJO - comando nuevo sin dependencias | `--format raw` |
| `segment_id` | Ya conocido por CLI | BAJO | `--format raw` |
| `timing_ms` | Siempre 0 para session (no tiene latencia) | BAJO | `--format raw` |
| `warnings` | Siempre vacío para session | BAJO | `--format raw` |

**Evidencia** (FINAL_PROPOSAL:L29-L33):
> **Campos ELIMINADOS del output**:  
> - `run_id` (irrelevante para session context)  
> - `segment_id` (ya conocido por CLI)  
> - `timing_ms` (siempre 0 para session)  
> - `warnings` (siempre vacío para session)

**Reducción estimada**: ~40% menos tokens por entry (FINAL_PROPOSAL:L48)

**IMPORTANTE**: Estos campos **siguen existiendo** en `_ctx/telemetry/events.jsonl`. Solo se ocultan en output limpio.

**Acceso completo**:
```bash
# Output limpio (sin campos telemetry)
trifecta session query -s . --last 5 --format clean

# Output raw (todos los campos)
trifecta session query -s . --last 5 --format raw
```

**Riesgo de contrato**: BAJO porque:
1. `session query` es comando NUEVO (no hay dependencias existentes)
2. `--format raw` preserva acceso completo
3. Schema clean es opt-in por defecto, no rompe nada

---

## 5) BLOCKERS (NO-PASS) — LISTA BRUTAL

### BLOCKER #1: Dual Write Obligatorio (CRÍTICO)
**Causa**: Si V1 solo escribe a telemetry.jsonl → session.md deja de actualizarse → rompe 3 tests  
**Evidencia**: AUDIT:L196-L203  
**Fix mínimo**:
```python
# src/infrastructure/cli.py:session_append
telemetry.event(cmd="session.entry", ...)  # NEW
with open(session_file, "a") as f:  # KEEP
    f.write(entry_text)
```
**Test/Gate**: `pytest tests/unit/test_session_and_normalization.py -v` → MUST PASS 3/3

---

### BLOCKER #2: JSON Schema en Archivos Separados
**Causa**: Schema solo existe en markdown (SCOOP), no como `.schema.json` validable  
**Evidencia**: AUDIT:L153-L156, L188-L190  
**Fix mínimo**: Crear `docs/schemas/session_query_clean.schema.json` + validator test  
**Test/Gate**: `pytest tests/integration/test_session_query_schema.py -v`

---

### BLOCKER #3: Benchmark Determinista
**Causa**: Propuesta usa `time | grep` (no parseable, no determinista)  
**Evidencia**: AUDIT:L236-L250  
**Fix mínimo**: Script Python con `np.percentile()` → output JSON  
**Test/Gate**: `scripts/bench_session_query.py` → p95 < 100ms

---

### BLOCKER #4: Token vs Bytes (Ambigüedad de Spec)
**Causa**: "40% reducción" usa `wc -w` (words ≠ tokens), no especifica tokenizer  
**Evidencia**: AUDIT:L316-L356, FINAL_PROPOSAL:L48 ("~40%")  
**Fix mínimo**: Decidir bytes (simple) o tokens (especificar tokenizer: tiktoken/gpt-4)  
**Test/Gate**: Script de medición determinista

---

### BLOCKER #5: Dataset Generator No Existe
**Causa**: `scripts/generate_benchmark_dataset.py` mencionado pero no implementado  
**Evidencia**: AUDIT:L363-L373  
**Fix mínimo**: Crear script que genere 10K events sintéticos  
**Test/Gate**: `wc -l /tmp/bench.jsonl` → 10000

---

### BLOCKER #6: Privacy Sanitization No Verificada
**Causa**: No se verificó que `_sanitize_event` cubre `args.files` de `session.entry`  
**Evidencia**: AUDIT:L497-L513  
**Fix mínimo**: Inspeccionar `_sanitize_event` (telemetry.py:L49) + test  
**Test/Gate**: `tests/acceptance/test_no_privacy_leaks.py -v`

---

### BLOCKER #7: Privacy Tests Ausentes
**Causa**: No hay test automatizado que valide no-leak de paths absolutos  
**Evidencia**: AUDIT:L517-L571  
**Fix mínimo**: Crear acceptance test con regex `/Users/|/home/|C:\\Users\\`  
**Test/Gate**: `pytest tests/acceptance/test_no_privacy_leaks.py::test_session_query_no_absolute_paths -v`

---

### BLOCKER #8: Backward Compatibility de Output
**Causa**: Propuesta cambia output de text a JSON → rompe scripts que parsean  
**Evidencia**: AUDIT:L125-L151  
**Fix mínimo**: Mantener output text + añadir opcional `(entry: session:ID)`  
**Test/Gate**: Verificar que output sigue siendo text, NO JSON

**Output actual** (debe mantenerse):
```
✅ Appended to _ctx/session_trifecta_dope.md
   Summary: <text>
```

**Output propuesto ERRÓNEO** (rompe compat):
```json
{"status": "ok", "message": "...", "entry_id": "..."}
```

**Fix**:
```
✅ Appended to _ctx/session_trifecta_dope.md (entry: session:abc123)
   Summary: <text>
```

---

## 6) RECOMENDACIÓN (MÍNIMO CAMBIO VIABLE)

### Opción A: Dual Write Obligatorio (RECOMENDADO)

**Decisión**: V1 escribe a AMBOS destinos (telemetry.jsonl + session.md)

**Rationale**:
1. ✅ Mantiene backward compatibility 100%
2. ✅ Tests existentes pasan sin modificar
3. ✅ session.md sigue siendo historia humana legible
4. ✅ telemetry.jsonl se vuelve queryable source of truth
5. ✅ Cero regresión, solo extensión

**Implementación**:
```python
def session_append(...):
    # NUEVA Lógica: Write to telemetry
    telemetry.event(
        cmd="session.entry",
        args={"summary": summary, "type": "develop", "files": files_list, "commands": commands_list},
        result={"outcome": "success"},
        timing_ms=0,
        tags=[]
    )
    
    # EXISTENTE: Write to session.md (NO TOCAR)
    if not session_file.exists():
        session_file.write_text(header + entry_text)
    else:
        with open(session_file, "a") as f:
            f.write(entry_text)
    
    # Output text (backward compat)
    typer.echo(f"✅ Appended to {session_file.relative_to(segment_path)}")
```

**Gate**: `pytest tests/unit/test_session_and_normalization.py -v` → 3/3 PASS

---

### Opción B: JSONL Source of Truth + Generator (NO RECOMENDADO para V1)

**Decisión**: V1 solo escribe a telemetry, session.md generado desde JSONL

**Problemas**:
1. ❌ Rompe 3 tests existentes
2. ❌ Requiere script generator (2h extra)
3. ❌ session.md deja de ser editable manual
4. ❌ Pérdida de historia si generator falla

**Recomendación**: POSTPONER a V2 (después de validar que dual write funciona)

**Evidencia de decisión** (braindope:L462-L476):
> DECISIONES CONVERGIDAS:  
> 3. session.md se mantiene → Sincronizado con JSONL (puede generarse)

**PERO** sincronización en V1 = dual write, NO generator (generador es V2)

---

### DECISIÓN FINAL BASADA EN EVIDENCIA

**ELIJO**: **Opción A (Dual Write)**

**Razones**:
1. ✅ AUDIT:L95 recomienda explícitamente dual write
2. ✅ braindope:L468 usuario decidió "mantener session.md"
3. ✅ FINAL_PROPOSAL:L135-L140 menciona "append a telemetry + sync md"
4. ✅ Cero tests rotos
5. ✅ Camino más seguro (fail-closed)

**Evidencia que confirma dual write es la decisión**:
> FINAL_PROPOSAL:L134-L136:  
> # Hace DOS cosas:  
> # 1. Append a telemetry.jsonl (source of truth)  
> # 2. Regenera session.md DESDE telemetry (opcional, si --sync-md flag)

**INTERPRETACIÓN CORRECTA**: 
- V1: Dual write (ambos) 
- V2: Opcional `--sync-md` flag para regenerar completo desde JSONL

---

## RESUMEN EJECUTIVO

### ✅ QUÉ NO SE BORRA
- session append (se extiende)
- session.md (se mantiene actualizado)
- telemetry.jsonl (se reutiliza)

### 💀 QUÉ SE DESCARTA (nunca existió)
- session_journal.jsonl separado
- Auto-detección de tool use
- Background daemon
- session query/load (comandos NUEVOS, no borrados)

### 🔵 QUÉ SE FILTRA (no es borrado)
- Campos telemetry en output clean (run_id, timing_ms, etc.)
- Accesibles con `--format raw`

### 🚫 BLOCKERS (8 total)
1. Dual write obligatorio
2. JSON schemas faltantes
3. Benchmark no determinista
4. Token vs bytes ambiguo
5. Dataset generator no existe
6. Privacy sanitization no verificada
7. Privacy tests ausentes
8. Output backward compat

### ✅ CAMINO SEGURO
**V1**: Dual write (telemetry + session.md) → cero regresión, solo extensión  
**V2**: Opcional generator desde JSONL → después de validar V1

---

**CONCLUSIÓN**: No se borra ninguna feature existente. El único riesgo era session.md congelado, mitigado con dual write obligatorio.

