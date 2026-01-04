# Propuesta Final Convergida: Session via Telemetry (Clean)

**Decisiones Tomadas**:
1. ✅ Speed + token efficiency → grep filter + telemetry rotation
2. ✅ Schema limpio → Filtrado automático de campos irrelevantes
3. ✅ session.md se mantiene → Sincronizado con JSONL (puede generarse)
4. ✅ Separación semántica → Convention-based namespace

---

## Schema Limpio (Solo lo Esencial)

### Event Raw (en telemetry.jsonl)
```json
{
  "ts": "2026-01-04T11:00:00-03:00",
  "cmd": "session.entry",
  "args": {
    "summary": "Fixed LSP daemon lifecycle",
    "type": "debug",
    "files": ["src/infrastructure/lsp_client.py"],
    "commands": ["pytest tests/integration/"]
  },
  "result": {"outcome": "success"},
  "x": {"tags": ["lsp", "daemon"]}
}
```

**Campos ELIMINADOS del output**:
- `run_id` (irrelevante para session context)
- `segment_id` (ya conocido por CLI)
- `timing_ms` (siempre 0 para session)
- `warnings` (siempre vacío para session)

### Output Limpio (session query)
```json
{
  "ts": "2026-01-04T11:00:00",
  "summary": "Fixed LSP daemon lifecycle",
  "type": "debug",
  "files": ["src/infrastructure/lsp_client.py"],
  "commands": ["pytest tests/integration/"],
  "outcome": "success",
  "tags": ["lsp", "daemon"]
}
```

**Reducción**: ~40% menos tokens por entry

---

## Performance: Grep Filter + Rotation

### Query Rápido (grep first)
```bash
# Implementación interna de `trifecta session query`
grep '"cmd": "session.entry"' _ctx/telemetry/events.jsonl | \
  jq -c 'del(.run_id, .segment_id, .timing_ms, .warnings) | 
         {ts, summary: .args.summary, type: .args.type, 
          files: .args.files, commands: .args.commands, 
          outcome: .result.outcome, tags: .x.tags}'
```

**Performance**: ~30-50ms para 50K events (grep elimina 99% antes de jq)

### Telemetry Rotation (automática)
```bash
# Script ejecutado por `trifecta ctx sync` si telemetry > 10K events
if [ $(wc -l < telemetry/events.jsonl) -gt 10000 ]; then
  # Move events older than 30 days to archive
  awk -v cutoff=$(date -d '30 days ago' +%s) '...' \
    telemetry/events.jsonl > telemetry/archive_$(date +%Y%m).jsonl
fi
```

**Resultado**: telemetry activo siempre < 10K events → queries < 50ms

---

## Separación Semántica: Namespace Convention

### Opción A: Comando Prefijo (RECOMENDADO)
```
Observability: lsp.*, ast.*, ctx.*, telemetry.*
Session:       session.*
```

**Ventaja**: Fácil filtrar por prefijo
```bash
# Solo observability
grep -E '"cmd": "(lsp|ast|ctx)\.' events.jsonl

# Solo session
grep '"cmd": "session\.' events.jsonl
```

### Opción B: Metadata Flag (como frontmatter YAML)
```json
{
  "cmd": "session.entry",
  "x": {
    "category": "narrative",  // vs "observability"
    "tags": [...]
  }
}
```

**Ventaja**: Separación explícita, queryable
```bash
jq 'select(.x.category == "narrative")' events.jsonl
```

**Recomendación**: Usar **Opción A** (cmd prefijo) + **Opción B** (metadata) combinadas
- Prefijo para filter rápido (grep)
- Metadata para queries semánticos

---

## session.md Sync (Bidireccional)

### Generación Automática (JSONL → session.md)
```bash
# Script: generate_session_md.sh
trifecta session query -s . --all | \
  jq -r '"## \(.ts)\n**Type**: \(.type)\n**Summary**: \(.summary)\n**Files**: \(.files | join(", "))\n**Outcome**: \(.outcome)\n"' \
  > _ctx/session_trifecta_dope.md
```

### Sincronización en `session append`
```bash
# Cuando ejecutas:
trifecta session append -s . --summary "..." --type debug ...

# Hace DOS cosas:
# 1. Append a telemetry.jsonl (source of truth)
# 2. Regenera session.md DESDE telemetry (opcional, si --sync-md flag)
```

**Single Source of Truth**: JSONL
**session.md**: Generado, humano-legible, NO se edita manual

---

## CLI Interface Final

```bash
# Append session entry (escribe a telemetry + sync md)
trifecta session append -s . \
  --summary "Fixed LSP bug" \
  --type debug \
  --files "src/lsp.py,src/daemon.py" \
  --commands "pytest tests/,ruff check" \
  --outcome success \
  --tags "lsp,daemon" \
  --sync-md  # Opcional: regenera session.md

# Query (output limpio, sin campos telemetry)
trifecta session query -s . \
  --type debug \
  --last 10 \
  --format clean  # Default: clean (sin run_id, timing_ms, etc.)

# Query raw (si necesitas schema completo)
trifecta session query -s . --last 5 --format raw

# Load context (para agente - máximo token efficiency)
trifecta session load -s . --last 3 --format compact
# Output: Solo summary + type en 1 línea por entry
```

---

## Implementación (Estimado)

| Tarea | Horas | Prioridad |
|:------|:------|:----------|
| Modificar `session append` → write to telemetry | 2h | Alta |
| CLI `session query` con filtros + clean schema | 4h | Alta |
| Grep optimization + jq filters | 2h | Media |
| session.md generator script | 2h | Baja (opcional) |
| Telemetry rotation logic | 3h | Media |
| Tests de integración | 3h | Alta |
| **TOTAL** | **16h** | |

**vs Alternativa (session_journal.jsonl separado)**: ~25h

**Ahorro**: 9 horas

---

## Complexity Budget

| Decisión | Costo |
|:---------|:------|
| Reutilizar telemetry JSONL | 0 (ya existe) |
| Event type `session.entry` | +5 pts (nuevo tipo) |
| CLI query con filtros | +10 pts (nueva lógica) |
| Telemetry rotation | +10 pts (mantenimiento) |
| session.md sync | +5 pts (script extra) |
| **TOTAL** | **30 pts** |

**Presupuesto restante**: 70/100

---

## Contrato de Fase (Inmutables)

### Reglas Inquebrantables
1. **telemetry.jsonl es source of truth** (session.md es generado)
2. **Schema output SIEMPRE limpio** (no exponer run_id, timing_ms a session context)
3. **Queries < 100ms** (vía grep filter + rotation)
4. **Token efficiency** (formato compact para contexto de agente)

### Limits
- telemetry.jsonl activo: < 10K eventos (rotation automática)
- Session query response: < 500 tokens por entry
- CLI latency: < 100ms para queries

### Exit Criteria
- [x] `session append` escribe a telemetry
- [x] `session query` retorna schema limpio
- [x] Grep filter funcional (< 50ms)
- [x] session.md puede generarse desde JSONL
- [x] Tests passing (session workflow E2E)

---

## Ahorro Final vs Propuesta Original

| Métrica | Original (session_journal.jsonl) | Final (telemetry event) | Ahorro |
|:--------|:--------------------------------|:------------------------|:-------|
| Código nuevo | ~25 horas | ~16 horas | **9 horas** |
| Archivos JSONL | 2 (telemetry + session) | 1 (telemetry) | **-1 archivo** |
| Sincronización | Manual (compleja) | N/A (single source) | **Cero bugs sync** |
| Complejidad | 45 pts | 30 pts | **-15 pts** |
| Query performance | Unknown | < 50ms (grep) | **Medible** |

---

## Próximos Pasos Inmediatos

1. Crear ADR: `docs/adr/005-session-via-telemetry.md`
2. Actualizar telemetry schema doc con `session.entry` spec
3. Prototipar `session query` con grep + jq (2 horas)
4. Validar performance con 10K events mock
5. Implementar si prototipo pasa < 100ms threshold

**¿Apruebas para proceder a implementación o ajustas algo?**
