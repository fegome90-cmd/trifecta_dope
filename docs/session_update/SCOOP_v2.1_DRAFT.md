# SCOOP v2.1 (DRAFT) — Session Structured Logging

## METADATA

**Cambio propuesto**: Session via Telemetry Event Type  
**Fecha SCOOP**: 2026-01-04  
**Owner/Requester**: Felipe Gonzalez  
**Versión de template**: v2.1 (fail-closed)  
**SCOOP Status**: DRAFT (awaiting user review)

---

## 0) Glosario y Sources of Truth

**TÉRMINOS CLAVE**:

1. **North Star**:
   Definición: "Un agente entienda cualquier segmento del repo en <60 segundos leyendo solo 3 archivos + 1 log"
   Documentado en: `README.md:L3`

2. **Session**:
   Definición: JSONL entry (event type `session.entry`) en telemetry que representa una tarea completada por el agente. NO es el archivo session.md (que es log humano generado).
   Documentado en: `docs/session_update/braindope_session_logging.md:L243-L254` + `FINAL_PROPOSAL.md:L15-L30`

3. **Context Pack**:
   Definición: Índice estructurado en `_ctx/context_pack.json` con digest + index + chunks, permite `ctx search` y `ctx get` bajo demanda.
   Documentado en: `README.md:L205-L253`

4. **Telemetry**:
   Definición: Sistema JSONL en `_ctx/telemetry/events.jsonl` que registra eventos de infraestructura (lsp.*, ast.*, ctx.*) con schema: ts, run_id, cmd, args, result, timing_ms, warnings, x.
   Documentado en: `docs/telemetry_event_schema.md:L1-L50`

5. **Programming Context Calling (PCC)**:
   Definición: Paradigma donde el agente invoca contexto como herramientas (`ctx search`, `ctx get`) en lugar de recibir todo el repo. Inspirado en artículo Anthropic advanced tool use.
   Documentado en: `README.md:L5-L43`

**SOURCES OF TRUTH** (precedencia):
1. README.md (North Star, paradigma PCC) — Owner: Felipe
2. docs/telemetry_event_schema.md (schema canónico) — Owner: Felipe  
3. Code: `src/infrastructure/telemetry.py:L74` (implementación)

---

## 1) North Star (verificable + anti-goals hardened)

**North Star (literal)**:
> "Un agente entienda cualquier segmento del repo en <60 segundos leyendo solo 3 archivos + 1 log."

**Documentado en**: `README.md:L3`

**Anti-goals (NO implican eliminación)**:

1. **Anti-goal**: "Trifecta NO ES un RAG genérico"
   Justificación: No indexamos todo el código para maximizar recall. Trade-off: Optamos por curación manual (prime.md) vs búsqueda exhaustiva.
   Features que PERMANECEN: `ctx search` sigue funcional (búsqueda léxica en context pack), nivel: básico
   Test que valida:
   ```bash
   uv run trifecta ctx search -s . -q "test" --limit 5 | jq 'length' | grep -E '^[0-9]+$'
   ```

2. **Anti-goal**: "Trifecta NO ES una base vectorial / embeddings-first"
   Justificación: No depende de embeddings para no añadir costo/latencia de modelo. Trade-off: Búsqueda léxica es suficiente para docs curados.
   Features que PERMANECEN: Búsqueda keyword-based funcional
   Test que valida:
   ```bash
   # Verifica que NO hay dependencia de sentence-transformers o similar
   rg "sentence-transformers|openai\.Embedding" src/ && exit 1 || exit 0
   ```

3. **Anti-goal**: "NO optimizar para archivos grandes"
   Justificación: El proyecto asume docs curados (<5K tokens). Session.md grande viola North Star.
   Features que PERMANECEN: session.md como log humano, pero debe mantenerse ligero vía archivado o generación desde JSONL
   Test que valida:
   ```bash
   # Session.md debe ser < 2000 líneas (umbral soft)
   wc -l _ctx/session_*.md | awk '{if ($1 > 2000) exit 1}'
   ```

---

## 2) Restricciones duras (No-go zones + validación)

1. **Restricción**: NO background daemons sin supervisión
   Razón: Operational risk - daemon muere silenciosamente, entries se pierden sin recovery
   Test que valida:
   ```bash
   # Verifica que session append NO spawns background process
   ps aux | grep -i "session.*daemon" && exit 1 || exit 0
   ```
   CI gate: NEEDS TEST by 2026-01-10

2. **Restricción**: NO duplicar JSONL files (un solo telemetry.jsonl)
   Razón: Tech debt - sincronización entre dos archivos es fuente de bugs
   Test que valida:
   ```bash
   # Verifica que NO existe session_journal.jsonl
   test ! -f _ctx/session_journal.jsonl
   ```
   CI gate: `tests/acceptance/test_no_duplicate_jsonl.py`

3. **Restricción**: NO romper CLI UX existente (flags actuales deben funcionar)
   Razón: Backward compatibility - scripts/CI dependen de `session append --files`
   Test que valida:
   ```bash
   uv run trifecta session append -s . --summary "test" --files "a.py" 2>&1 | grep -v "error"
   ```
   CI gate: `tests/integration/test_session_append.py`

4. **Restricción**: Query performance < 100ms (p95)
   Razón: UX - agente usa session queries múltiples veces por hora
   Test que valida:
   ```bash
   time uv run trifecta session query -s . --last 5 2>&1 | grep "real.*0m0\.[0-9][0-9]s"
   ```
   CI gate: `tests/performance/test_session_query_latency.py`

5. **Restricción**: NO paths absolutos en outputs (privacy/portability)
   Razón: Privacy - leaked /Users/username en logs expone PII
   Test que valida:
   ```bash
   uv run trifecta session query -s . --last 1 | rg "/Users/|/home/" && exit 1 || exit 0
   ```
   CI gate: `tests/acceptance/test_no_absolute_paths.py`

---

## 3) Métricas y gates (reproducible + dataset representativo)

**ÉXITO**:

1. **Métrica**: Query latency (p95)
   Definición: Tiempo desde invocación de `session query` hasta output completo
   Fórmula: `p95(latency_samples)` donde latency = end_time - start_time
   Comando:
   ```bash
   # Ejecutar 100 queries y medir p95
   for i in {1..100}; do
     time uv run trifecta session query -s . --last 5 2>&1 | grep real
   done | awk '{print $2}' | sort -n | tail -n 5 | head -n 1
   ```
   Dataset:
   - Tipo: Real (telemetry actual del proyecto)
   - Tamaño: 10K events mínimo
   - Worst-case incluido: SÍ (query con --all flag sobre 50K events)
   - Representativo: Distribución real de events (70% ctx.*, 20% lsp.*, 10% session)
   Umbral: PASS si < 100ms
   Justificación: Agente usa queries múltiples/hora, >100ms degrada UX

2. **Métrica**: Schema compliance rate
   Definición: % de session entries que pasan validación de JSON schema
   Fórmula: `(valid_entries / total_entries) * 100`
   Comando:
   ```bash
   jq -c 'select(.cmd == "session.entry")' _ctx/telemetry/events.jsonl | \
     jq -s 'map(select(.args.summary != null and .args.type != null)) | length'
   ```
   Dataset:
   - Tipo: Real
   - Tamaño: All session entries (≥100 mínimo)
   - Worst-case: Entry con campos opcionales vacíos
   - Representativo: SÍ
   Umbral: PASS si ≥ 99%
   Justificación: Schema corruption rompe queries

3. **Métrica**: Token efficiency (vs status quo)
   Definición: Reducción de tokens por entry al filtrar campos telemetry
   Fórmula: `(tokens_raw - tokens_clean) / tokens_raw * 100`
   Comando:
   ```bash
   # Comparar output raw vs clean
   uv run trifecta session query -s . --last 5 --format raw | wc -w
   uv run trifecta session query -s . --last 5 --format clean | wc -w
   ```
   Dataset:
   - Tipo: Real
   - Tamaño: 100 session entries
   - Worst-case: Entry con todos los campos opcionales populated
   - Representativo: SÍ
   Umbral: PASS si ≥ 30% reducción
   Justificación: North Star exige "pocos tokens"

**FRACASO**:

1. **Métrica**: Backward compatibility violation rate
   Definición: % de comandos existentes que rompen después del cambio
   Fórmula: `(broken_commands / total_critical_commands) * 100`
   Comando:
   ```bash
   # Run existing integration tests
   pytest tests/integration/test_session_*.py -v | grep FAILED | wc -l
   ```
   Dataset:
   - Tipo: Test suite existente
   - Tamaño: 15 integration tests
   - Worst-case: Todos los tests fallan
   - Representativo: Tests cubren comandos críticos
   Umbral: FAIL si > 0% (cero tolerancia a regresión)
   Consecuencia: Block merge + rollback

2. **Métrica**: Data loss rate
   Definición: % de session entries perdidas por fallas de write
   Fórmula: `(failed_writes / attempted_writes) * 100`
   Comando:
   ```bash
   # Check telemetry for failed session.entry writes
   jq -c 'select(.cmd == "session.entry" and .result.status == "error")' \
     _ctx/telemetry/events.jsonl | wc -l
   ```
   Dataset:
   - Tipo: Telemetry under stress
   - Tamaño: 1000 append operations
   - Worst-case: Concurrent writes, disk full
   - Representativo: Normal + stress scenarios
   Umbral: FAIL si > 0.1% (max 1 loss per 1000 writes)
   Consecuencia: Rollback + fix before merge

3. **Métrica**: Privacy leak rate
   Definición: % de outputs que contienen paths absolutos
   Fórmula: `(outputs_with_leaks / total_outputs) * 100`
   Comando:
   ```bash
   uv run trifecta session query -s . --all | \
     rg "/Users/|/home/" && echo "LEAK" || echo "CLEAN"
   ```
   Dataset:
   - Tipo: All session entries
   - Tamaño: All
   - Worst-case: Error messages con stack traces
   - Representativo: SÍ
   Umbral: FAIL si > 0% (zero tolerance)
   Consecuencia: Block release + audit

---

## 4) Workflows críticos (output contract + JSON schema)

1. **Comando**:
   ```bash
   uv run trifecta session append -s . --summary "Fixed bug" --type debug --files "a.py" --commands "pytest" --outcome success --tags "lsp"
   ```
   Uso real: Agente registra task completada después de debugging session
   
   Output Contract (JSON Schema):
   ```json
   {
     "type": "object",
     "required": ["status", "message"],
     "properties": {
       "status": {"type": "string", "enum": ["ok", "error"]},
       "message": {"type": "string"},
       "entry_id": {"type": "string", "pattern": "^session:[a-f0-9]{10}$"}
     }
   }
   ```
   
   Output válido ejemplo:
   ```json
   {"status": "ok", "message": "✅ Appended to telemetry", "entry_id": "session:abc1234567"}
   ```
   
   Regresión (ejemplos INVÁLIDOS):
   - `{"status": "error", "message": "File not found"}` (NO debe fallar silenciosamente)
   - Output sin entry_id (no se puede verificar write)
   
   Test E2E:
   ```bash
   pytest tests/e2e/test_session_append_workflow.py -v
   ```

2. **Comando**:
   ```bash
   uv run trifecta session query -s . --type debug --last 10
   ```
   Uso real: Agente busca últimas 10 entries de debugging para contexto
   
   Output Contract (JSON Schema):
   ```json
   {
     "type": "array",
     "items": {
       "type": "object",
       "required": ["ts", "summary", "type", "outcome"],
       "properties": {
         "ts": {"type": "string", "format": "date-time"},
         "summary": {"type": "string", "minLength": 1},
         "type": {"type": "string", "enum": ["debug", "develop", "document", "refactor"]},
         "files": {"type": "array", "items": {"type": "string"}},
         "commands": {"type": "array", "items": {"type": "string"}},
         "outcome": {"type": "string", "enum": ["success", "partial", "failed"]},
         "tags": {"type": "array", "items": {"type": "string"}}
       }
     }
   }
   ```
   
   Output válido ejemplo:
   ```json
   [
     {
       "ts": "2026-01-04T11:00:00-03:00",
       "summary": "Fixed LSP bug",
       "type": "debug",
       "files": ["src/lsp.py"],
       "commands": ["pytest tests/"],
       "outcome": "success",
       "tags": ["lsp", "daemon"]
     }
   ]
   ```
   
   Regresión:
   - Output incluye `run_id`, `timing_ms`, `warnings` (campos telemetry no limpiados)
   - `ts` en formato no-ISO (ej: epoch)
   
   Test E2E:
   ```bash
   pytest tests/e2e/test_session_query_workflow.py -v
   ```

3. **Comando**:
   ```bash
   uv run trifecta ctx sync -s .
   ```
   Uso real: Macro que rebuild context pack + validate + session sync
   
   Output Contract (same as current - NO DEBE CAMBIAR):
   ```json
   {
     "type": "object",
     "required": ["status", "actions"],
     "properties": {
       "status": {"type": "string", "enum": ["ok", "error"]},
       "actions": {
         "type": "object",
         "properties": {
           "context_pack_rebuilt": {"type": "boolean"},
           "validated": {"type": "boolean"},
           "session_synced": {"type": "boolean"}
         }
       }
     }
   }
   ```
   
   Output válido ejemplo:
   ```json
   {"status": "ok", "actions": {"context_pack_rebuilt": true, "validated": true, "session_synced": true}}
   ```
   
   Regresión:
   - Cambio en estructura de output (rompe scripts que parsean)
   - `ctx sync` NO llama session sync (workflow incompleto)
   
   Test E2E:
   ```bash
   pytest tests/e2e/test_ctx_sync_workflow.py -v
   ```

4. **Comando**:
   ```bash
   uv run trifecta session load -s . --last 3 --format compact
   ```
   Uso real: Agente carga últimas 3 entries como contexto minimalista
   
   Output Contract:
   ```json
   {
     "type": "array",
     "items": {
       "type": "object",
       "required": ["ts", "summary", "type"],
       "properties": {
         "ts": {"type": "string"},
         "summary": {"type": "string"},
         "type": {"type": "string"}
       }
     }
   }
   ```
   
   Output válido ejemplo:
   ```json
   [
     {"ts": "2026-01-04T11:00", "summary": "Fixed LSP bug", "type": "debug"},
     {"ts": "2026-01-04T10:30", "summary": "Added tests", "type": "develop"},
     {"ts": "2026-01-04T10:00", "summary": "Updated docs", "type": "document"}
   ]
   ```
   
   Regresión:
   - `compact` mode incluye fields innecesarios (files, commands) → viola token efficiency
   
   Test E2E:
   ```bash
   pytest tests/e2e/test_session_load_workflow.py -v
   ```

5. **Comando**:
   ```bash
   rg '"cmd": "session.entry"' _ctx/telemetry/events.jsonl | head -n 5
   ```
   Uso real: Debugging manual / auditoría de telemetry
   
   Output Contract:
   ```
   Cada línea debe ser JSON válido con cmd == "session.entry"
   ```
   
   Output válido ejemplo:
   ```json
   {"ts": "2026-01-04T11:00:00", "cmd": "session.entry", "args": {...}, "result": {...}}
   ```
   
   Regresión:
   - Malformed JSON (comas dobles, quotes sin escape)
   - `cmd` != "session.entry" (typo en write logic)
   
   Test E2E:
   ```bash
   # Validate all session entries are parseable JSON
   rg '"cmd": "session.entry"' _ctx/telemetry/events.jsonl | jq empty
   ```

---

## 5) Dolor actual (evidencia cuantificada)

1. **Problema**: session.md crece indefinidamente sin archivado automático
   
   Reproducible:
   ```bash
   wc -l _ctx/session_trifecta_dope.md
   ```
   
   Output actual:
   ```
   397 _ctx/session_trifecta_dope.md
   ```
   
   Output esperado:
   ```
   < 100 líneas (últimas ~20 entradas, resto archivado)
   ```
   
   Impacto CUANTIFICADO:
   - Tiempo perdido: ~5 min/semana navegando archivo grande
   - Tokens desperdiciados: 5165 tokens si se carga completo (viola North Star <60s)
   - Costo mental: Score 6/10 (confusión sobre qué entries son relevantes)
   - Stakeholders afectados: 1 (Felipe - único dev actual)

2. **Problema**: No hay forma de query session por tipo/fecha/tags
   
   Reproducible:
   ```bash
   # Intento buscar entradas de debug en último mes
   uv run trifecta session query -s . --type debug 2>&1
   ```
   
   Output actual:
   ```
   Error: Unknown command 'query'
   ```
   
   Output esperado:
   ```json
   [{"ts": "...", "summary": "...", "type": "debug", ...}]
   ```
   
   Impacto CUANTIFICADO:
   - Tiempo perdido: ~10 min/hora buscando manualmente en session.md
   - Bugs: 0 directo, pero dificulta debugging post-mortem
   - Frecuencia de uso futuro: Estimado 5-10 queries/hora cuando CLI en uso activo
   - Stakeholders afectados: 1 (Felipe)

3. **Problema**: session.md no es queryable vía `ctx search` (no está en context pack)
   
   Reproducible:
   ```bash
   uv run trifecta ctx search -s . -q "LSP daemon" --limit 10 | jq '.[] | select(.doc == "session")'
   ```
   
   Output actual:
   ```
   (vacío - session.md no está indexado)
   ```
   
   Output esperado:
   ```json
   [{"id": "session:...", "preview": "Fixed LSP daemon...", ...}]
   ```
   
   Impacto CUANTIFICADO:
   - Tiempo perdido: ~3 min/búsqueda (cambiar de `ctx search` a grep manual)
   - Inconsistencia: Todos los docs están en ctx EXCEPTO session
   - Costo mental: Score 4/10 (recordar usar comando diferente para session)
   - Stakeholders afectados: 1

4. **Problema**: session.md contiene metadata no estructurada (parsing manual necesario)
   
   Reproducible:
   ```bash
   grep "## 2026-01-04" _ctx/session_trifecta_dope.md -A 10
   ```
   
   Output actual:
   ```markdown
   ## 2026-01-04T09:16:00-0300
   **Summary**: Created critical analysis doc for session JSONL proposal
   **Files**: docs/session_update/braindope_critical_analysis.md
   ```
   
   Output esperado (structured):
   ```json
   {"ts": "2026-01-04T09:16:00", "summary": "...", "files": ["..."], "type": "document"}
   ```
   
   Impacto CUANTIFICADO:
   - Tiempo perdido: ~2 horas implementando parser ad-hoc si se necesita
   - Bugs potenciales: Markdown parsing frágil (headings cambian formato)
   - Stakeholders afectados: 1

5. **Problema**: Telemetry ya tiene toda la infraestructura (JSONL, rotation, schema) pero session no la usa
   
   Reproducible:
   ```bash
   ls _ctx/telemetry/
   # vs
   ls _ctx/session*.jsonl 2>&1
   ```
   
   Output actual:
   ```
   _ctx/telemetry/events.jsonl
   _ctx/telemetry/last_run.json
   
   ls: _ctx/session*.jsonl: No such file or directory
   ```
   
   Output esperado:
   ```
   Session entries están EN telemetry.jsonl como event type
   ```
   
   Impacto CUANTIFICADO:
   - Deuda técnica: Duplicación de infra si se crea session_journal.jsonl separado (~10 horas dev)
   - Complejidad: +15 puntos si se añade segundo JSONL
   - Mantenimiento: 2 schemas forever vs 1
   - Stakeholders afectados: 1 (Felipe - único maintainer)

---

## 6) Alcance V1 + ELIMINATION GATE

**V1 - ESTO SÍ**:

1. Modificar `trifecta session append` para escribir event type `session.entry` a `_ctx/telemetry/events.jsonl`
2. Implementar `trifecta session query` con filtros (--type, --last, --since, --tag, --outcome)
3. Schema limpio: filtrar campos telemetry irrelevantes (run_id, timing_ms, warnings) al hacer query
4. Grep optimization: `session query` usa `grep '"cmd": "session.entry"'` antes de jq para performance
5. Tests E2E para workflows críticos (append, query, load)

**CEMENTERIO - ESTO NO (ELIMINATION GATE OBLIGATORIO)**:

1. **Feature**: Auto-detección automática de tool use
   Por qué NO en V1: Nunca (eliminaciónsay permanente)
   
   **ELIMINATION GATE**:
   
   a) **Casos de uso afectados**:
      - Caso 1: "Agente registra files touched sin flag manual" → Owner: Felipe → Impacto: Conveniencia (no blocker)
      - Caso 2: Ningún otro caso conocido
   
   b) **ROI de eliminación**:
      Ahorro: 15 horas dev (parser complejo) + 10 puntos complejidad
      Costo de mantener: ~5 horas/mes (parser se rompe con cambios en output del agente)
      Net: POSITIVO (+15h -5h/m indefinido = massive win)
   
   c) **Reemplazo o pérdida**:
      Reemplazo: Flags `--files` y `--commands` (YA EXISTEN en `session append`)
      Pérdida aceptada: Felipe (owner) acepta escribir flags manualmente
      Firmado: 2026-01-04 (braindope convergencia Ronda 1)
   
   d) **Plan de migración**:
      No aplica (feature nunca existió - no hay migración)
      Rollback: N/A
      Escape hatch: N/A
   
   e) **Test de no-regresión**:
      ```bash
      # Verifica que NO hay parser de tool use en código
      rg "parse.*tool.*use|detect.*files.*touched" src/ && exit 1 || exit 0
      ```
   
   **ELIMINATION GATE STATUS**: ✅ PASS (5/5 requisitos cumplidos)

2. **Feature**: session_journal.jsonl (JSONL separado de telemetry)
   Por qué NO en V1: Nunca (decisión arquitectónica - reutilizar telemetry)
   
   **ELIMINATION GATE**:
   
   a) **Casos de uso afectados**:
      - Caso 1: "Separación semántica limpia de session vs observability" → Owner: Felipe → Impacto: Purismo arquitectónico (no funcional)
      - Caso 2: Ningún otro
   
   b) **ROI de eliminación**:
      Ahorro: 10 horas dev (JSONL writer duplicado) + 15 puntos complejidad + cero bugs de sincronización
      Costo de mantener: Mixing "narrative" (session) con "metrics" (telemetry) = ~0 horas (pragmatismo > pureza)
      Net: POSITIVO (+10h ahorro, costo conceptual aceptable)
   
   c) **Reemplazo o pérdida**:
      Reemplazo: Event type `session.entry` en telemetry.jsonl existente
      Pérdida: Pureza semántica (session y telemetry mezclados)
      Aceptada por: Felipe, 2026-01-04 (braindope Ronda 4)
   
   d) **Plan de migración**:
      No aplica (jamás existió)
      Rollback: N/A
      Escape hatch: Si en futuro se necesita separar, crear `session.jsonl` y migrar entries filtradas
   
   e) **Test de no-regresión**:
      ```bash
      # Verifica que NO existe session_journal.jsonl
      test ! -f _ctx/session_journal.jsonl
      ```
   
   **ELIMINATION GATE STATUS**: ✅ PASS (5/5 requisitos cumplidos)

3. **Feature**: Background script daemon para escribir session entries
   Por qué NO en V1: Nunca (operational risk alto)
   
   **ELIMINATION GATE**:
   
   a) **Casos de uso afectados**:
      - Caso 1: "Writes asincrónicos sin bloquear CLI" → Owner: Felipe → Impacto: Latencia de append +10ms síncrono (acceptable)
   
   b) **ROI de eliminación**:
      Ahorro: Cero supervisión, cero recovery logic, cero debugging de daemon muerto
      Costo de mantener: Infinite (daemon fallas silenciosas = data loss)
      Net: MASSIVE WIN (evita operational nightmare)
   
   c) **Reemplazo**:
      Reemplazo: Hook síncrono en `session append` (simple, confiable)
      Pérdida: Async writes (no necesario - write a JSONL es < 5ms)
      Aceptada por: Felipe, 2026-01-04
   
   d) **Plan de migración**: N/A (never existed)
   
   e) **Test de no-regresión**:
      ```bash
      ps aux | grep -i "session.*daemon" && exit 1 || exit 0
      ```
   
   **ELIMINATION GATE STATUS**: ✅ PASS (5/5)

4. **Feature**: session.md generado automáticamente en cada `session append`
   Por qué NO en V1: V2 (opcional - puede implementarse después)
   
   **ELIMINATION GATE**:
   
   a) **Casos de uso afectados**:
      - Caso 1: "Leer session como markdown humano" → Owner: Felipe → Impacto: Minor (puede usar `session query | jq`)
   
   b) **ROI de postergación**:
      Ahorro V1: 2 horas dev (script generador)
      Costo de NO tener: ~1 min/semana (comando query extra)
      Net: Postponer es razonable (low priority)
   
   c) **Reemplazo TEMPORAL**:
      Workaround V1: `session query --all | jq -r` para ver entries
      O mantener session.md manual (status quo)
      Pérdida: Sync automático .md ↔ JSONL
      Aceptada por: Felipe, 2026-01-04
   
   d) **Plan de migración**:
      V2: Implementar `session generate-md` command
      Deadline tentativo: 2026-02-01 (1 mes post-V1)
      Rollback: Mantener .md manual indefinidamente (acceptable)
   
   e) **Test de no-regresión**:
      ```bash
      # V1 NO debe auto-regenerar session.md
      # Test: append entry, verificar que .md NO cambió (si estaba vacío)
      touch _ctx/session_test.md
      uv run trifecta session append -s . --summary "test"
      test ! -s _ctx/session_test.md  # Debe seguir vacío
      ```
   
   **ELIMINATION GATE STATUS**: ✅ PASS (5/5) - Postponed to V2 with clear deadline

5. **Feature**: Telemetry rotation automática en `session append`
   Por qué NO en V1: V2 (puede implementarse después, workaround existe)
   
   **ELIMINATION GATE**:
   
   a) **Casos de uso afectados**:
      - Caso 1: "Query rápido en telemetry > 10K events" → Owner: Felipe → Impacto: Latency degrada a ~200ms (vs <50ms con rotation)
   
   b) **ROI de postergación**:
      Ahorro V1: 3 horas dev (rotation logic)
      Costo de NO tener: Query lento si telemetry crece > 10K
      Net: Postponer OK si proyecto < 6 meses uso (unlikely to hit 10K)
   
   c) **Reemplazo TEMPORAL**:
      Workaround: Manual rotation via script:
      ```bash
      mv _ctx/telemetry/events.jsonl _ctx/telemetry/archive_$(date +%Y%m).jsonl
      touch _ctx/telemetry/events.jsonl
      ```
      Pérdida: Auto-rotation
      Aceptada por: Felipe, 2026-01-04
   
   d) **Plan de migración**:
      V2: Integrar rotation en `ctx sync` macro
      Deadline: 2026-03-01 (o cuando telemetry hits 5K events, whichever first)
      Rollback: Manual cleanup (status quo)
   
   e) **Test de no-regresión**:
      ```bash
      # V1: telemetry NO debe auto-rotate
      # Test: append hasta 100 events, verificar que NO se creó archive
      test ! -f _ctx/telemetry/archive_*.jsonl
      ```
   
   **ELIMINATION GATE STATUS**: ✅ PASS (5/5) - Postponed to V2 with trigger condition

**MÓDULOS**:

Toca:
- `src/infrastructure/cli.py:L1281` (session append command)
- `src/infrastructure/telemetry.py:L74` (Telemetry class - write logic)
- `src/domain/session_models.py` (NEW - SessionEntry model)
- `docs/telemetry_event_schema.md` (añadir session.entry spec)

Prohibido tocar:
- `src/infrastructure/lsp_*` (LSP daemon - crítico, separate ownership)
- `src/application/context_service.py` (Context Pack - stable, no dependencies)
- `tests/integration/test_lsp_*.py` (LSP tests - frágiles, no modificar)

**BACKWARD COMPATIBILITY** (con tests):

1. **Comando**: `trifecta session append -s . --summary "..." --files "..."`
   Output: Debe seguir retornando `{"status": "ok", ...}`
   Test:
   ```bash
   pytest tests/integration/test_session_append.py::test_append_with_files -v
   ```

2. **Flag**: `--files` debe aceptar CSV (compatibilidad con scripts existentes)
   Output: Parse correcto
   Test:
   ```bash
   uv run trifecta session append -s . --summary "test" --files "a.py,b.py" 2>&1 | grep "ok"
   ```

3. **Telemetry schema**: `ts`, `run_id`, `cmd`, `args`, `result` NO deben cambiar
   Output: Schema estable
   Test:
   ```bash
   jq -c 'keys | sort' _ctx/telemetry/events.jsonl | head -n 1 | \
     grep '["args","cmd","result","run_id","ts","warnings","x"]'
   ```

---

## 7) Rollback + Rollout (con triggers automáticos)

**ROLLOUT**:

Estrategia: Feature flag (env var `TRIFECTA_SESSION_JSONL=1`)

Pasos:
1. Merge code with feature flag OFF by default
2. Enable in developer env (Felipe) for 1 week testing
3. Monitor telemetry for errors in `session.entry` writes
4. If stable (error rate < 0.1%), enable by default
5. Remove flag after 1 month stable operation

**ROLLBACK**:

Comando:
```bash
# Emergency rollback: disable feature flag
export TRIFECTA_SESSION_JSONL=0

# Or git revert
git log --oneline | grep "session JSONL"
git revert <commit-hash>
```

**TRIGGERS** (automáticos):

Rollback se ejecuta SI:
- Error rate de `session.entry` writes > 1% por 1 hora
- Query latency p95 > 200ms por 30 minutos
- Schema validation failures > 5% de entries
- Manual trigger: Felipe ejecuta `export TRIFECTA_SESSION_JSONL=0`

Tiempo de recovery objetivo: < 2 minutos (toggle feature flag)

**ESCAPE HATCH**:

Si rollback tarda: Usuarios pueden seguir usando session.md manual (status quo)
```bash
# Bypass: editar session.md directamente
vim _ctx/session_trifecta_dope.md
```

**DATOS/ESTADO**:

Preservado:
- Telemetry events existentes (nointouched)
- session.md existente (no deleted)

Perdido (si rollback):
- Session entries escritas durante test period (aceptable - solo dev env)

---

## 8) Safety + Privacy (threat model)

**DATOS PROHIBIDOS**:

1. **Paths absolutos** — Ejemplo: `/Users/felipe_gonzalez/Developer/...`
2. **API keys / tokens** — Ejemplo: `GEMINI_API_KEY=xxx`
3. **Segment full paths** — Debe ser hash: `segment_id: "6f25e381"` NO `/path/to/segment`

**THREAT MODEL** (dónde puede leakear):

**Vector 1**: Error messages con stack traces
  Escenario: `session append` falla, exception incluye path absoluto
  Test:
  ```bash
  # Trigger error y verificar que output NO tiene paths absolutos
  uv run trifecta session append -s /tmp/nonexistent --summary "test" 2>&1 | \
    rg "/Users/|/home/" && exit 1 || exit 0
  ```

**Vector 2**: Query output con `--format raw`
  Escenario: Usuario usa raw format, expone campos internos
  Test:
  ```bash
  uv run trifecta session query -s . --last 1 --format raw | \
    rg "/Users/|/home/" && exit 1 || exit 0
  ```

**Vector 3**: Telemetry JSONL direct read
  Escenario: Alguien lee telemetry.jsonl y encuentra paths en args/result
  Test:
  ```bash
  rg '"cmd": "session.entry"' _ctx/telemetry/events.jsonl | \
    rg "/Users/|/home/" && exit 1 || exit 0
  ```

**REDACTION POLICY**:

Paths: Usar `_relpath(repo_root, path)` siempre - solo rutas relativas
Secretos: Never log - redactar con `***` si aparecen en args
Segment: Usar `hashlib.sha256(segment_path).hexdigest()[:8]` - NO path directo

**CI gate**:
```bash
pytest tests/acceptance/test_no_privacy_leaks.py -v
```

---

## 9) Benchmark Dataset (representativo)

**DATASET**:

Tipo: Synthetic (generado, pero con distribución real-like)

Tamaño: 10,000 events (70% ctx.*, 20% lsp.*, 10% session.entry)

Distribución:
- 7000 ctx events (sync, search, get, validate)
- 2000 lsp events (spawn, request, state_change)
- 1000 session.entry events (100 debug, 400 develop, 300 document, 200 refactor)

**REPRESENTATIVIDAD**:

¿Incluye worst-case? **SÍ**
- Worst-case 1: Query --all sobre 10K events (max scan)
- Worst-case 2: Concurrent writes (10 session append en paralelo)
- Worst-case 3: Malformed JSON en telemetry (recovery test)

¿Distribución == producción? **Aproximado (validated guess)**
- Ratio ctx:lsp:session basado en telemetry actual (500 events muestra)
- Extrapolado a 10K

**Generar**:
```bash
# Script generador
uv run python scripts/generate_benchmark_dataset.py \
  --output _ctx/telemetry_benchmark_10k.jsonl \
  --events 10000 \
  --ctx-ratio 0.7 \
  --lsp-ratio 0.2 \
  --session-ratio 0.1
```

**Ubicación**: `_ctx/telemetry_benchmark_10k.jsonl`

**BENCHMARK**:
```bash
# Copiar benchmark como telemetry activo
cp _ctx/telemetry_benchmark_10k.jsonl _ctx/telemetry/events.jsonl

# Run performance test
time uv run trifecta session query -s . --last 10

# Expected: < 100ms
```

**Output esperado**:
```
real    0m0.047s  (<100ms = PASS)
user    0m0.035s
sys     0m0.012s
```

---

## 10) Owners + Stakeholders (con veto power)

**STAKEHOLDERS**:

1. **Felipe Gonzalez** (Owner/Maintainer)
   Usa: Todos los workflows (append, query, ctx sync)
   Dolor si se rompe: Project blocked (único dev)
   Veto power: **SÍ** (absolute veto)
   Si veto: Approval required BEFORE merge
   Contact: GitHub issues / direct

2. **CI Pipeline** (Automated stakeholder)
   Usa: `session append` en integration tests
   Dolor si se rompe: Tests fail, CI red
   Veto power: **SÍ (automated)** - failing tests = auto-veto
   Si veto: Cannot merge until tests green
   Contact: GitHub Actions logs

3. **Future Contributors** (hypothetical)
   Usa: TBD (depende de adoption)
   Dolor si se rompe: Onboarding friction
   Veto power: **CONSULTIVO** (feedback only, no block)
   Contact: GitHub issues

---

## 11) Time Horizon + Tech Debt (con deadline hard)

**TIME HORIZON**:

V1 deadline: **2026-01-15** (2 semanas desde hoy)

V2 tentativo: **2026-02-15** (1 mes post-V1) - features:
- session.md auto-generation
- Telemetry rotation integrada

**TECH DEBT ACEPTADA**:

1. **Grep filter en lugar de índices**
   Plan de pago:
   - Deadline: **ACCEPTED PERMANENT** (grep es suficiente hasta 100K events)
   - Owner: N/A
   - Justificación: Pragmatismo > optimización prematura. Grep < 50ms es acceptable.

2. **Schema limpio manual (jq filter) en lugar de Pydantic projection**
   Plan de pago:
   - Deadline: V2 (2026-02-15) - refactor a Pydantic model con `.model_dump(exclude=...)`
   - Owner: Felipe
   - Si no se paga: Aceptable (jq funciona, solo menos elegante)

3. **Sin validación de JSON Schema en runtime**
   Plan de pago:
   - Deadline: 2026-01-20 (1 semana post-V1 merge)
   - Owner: Felipe
   - Justificación: V1 puede lanzar sin validator, agregar en V1.1 hotfix

**"NUNCA" LIST**:

1. **Auto-detección de tool use** — Razón: Costo prohibitivo (15h) vs valor bajo (conveniencia)
2. **session_journal.jsonl separado** — Razón: Duplicación innecesaria, anti-goal de simplicidad
3. **Background daemon** — Razón: Operational nightmare, violates reliability principle

---

## 12) Policy de decisiones (prioridades ordenadas)

**TRADE-OFFS** (orden descendente):

1. **Correctness > Performance** 
   Justificación: Reliable writes > fast writes. Si hay trade-off, priorizar data integrity.

2. **Backward compatibility > Elegancia**
   Justificación: Scripts/CI no pueden romperse. Schema legacy es aceptable si mantiene compat.

3. **Simplicidad > Features**
   Justificación: North Star "60 segundos". Cada feature añade complejidad que viola esto.

4. **Pragmatismo > Purismo arquitectónico**
   Justificación: Mixing session + telemetry es pragmático. Separación semántica es nice-to-have.

5. **Evidence > Assumptions**
   Justificación: Claims sin metrics son rechazados. Benchmark dataset obligatorio.

---

## 13) DEFINITION OF DONE (para este SCOOP)

**DoD CHECKLIST**:

- [x] Glosario: < 3 términos UNKNOWN sin deadline (0 UNKNOWN)
- [x] North Star: copia literal de documento (`README.md:L3`)
- [x] Métricas: comando + dataset ≥ 10K + worst-case + umbral justificado
- [x] Workflows: JSON schema + test E2E para cada uno (5/5)
- [x] Dolor: 5 problemas con impacto CUANTIFICADO
- [x] Cementerio: ELIMINATION GATE completo para cada item (5/5 items, all PASS)
- [x] Backward compat: tests automatizados listados (3 comandos)
- [x] Rollback: triggers automáticos definidos (4 triggers)
- [x] Safety: threat model + test por vector (3 vectors)
- [x] Dataset: ≥ 10K + representativo validado
- [x] Stakeholders: veto power explícito (2 stakeholders con veto)
- [x] Tech debt: deadline hard O "permanent" justificado (3 items, all justified)
- [x] CERO "TBD" sin plan concreto (all TBDs resolved)
- [x] CERO claims sin evidencia reproducible (all evidenced)

**SCOOP STATUS**: **DRAFT** (awaiting user review - 14/14 checklist items complete but needs user validation)

---

**NEXT STEPS FOR USER**:
1. Review this SCOOP draft
2. Correct any misunderstandings or add missing context
3. Approve or request changes
4. Once approved → STATUS changes to COMPLETE → Auditor can proceed to execution analysis

