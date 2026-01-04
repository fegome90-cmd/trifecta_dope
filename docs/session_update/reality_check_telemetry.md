# Reality Check: ¿Es Telemetry la Respuesta?

**Fecha**: 2026-01-04  
**Análisis**: Brutal y Escéptico

---

## El Schema Actual de Telemetry

```json
{
  "ts": "2026-01-01T19:17:00-0300",
  "run_id": "run_1767305820",
  "segment_id": "6f25e381",
  "cmd": "lsp.spawn",
  "args": {"executable": "pylsp"},
  "result": {"status": "ok", "pid": 16994},
  "timing_ms": 1,
  "warnings": [],
  "x": {"lsp_state": "WARMING"}
}
```

**Granularidad**: Evento por COMANDO (ctx.search, lsp.spawn, ast.parse)  
**Propósito**: Observability - latencias, errores, métricas de performance

---

## Lo Que Session Necesita

```json
{
  "timestamp": "2026-01-04T09:50:21-03:00",
  "task_type": "debug",
  "summary": "Fixed LSP daemon lifecycle",
  "files_touched": ["src/infrastructure/lsp_client.py"],
  "tools_used": ["view_file", "replace_file_content"],
  "outcome": "success"
}
```

**Granularidad**: Entrada por TAREA/SESIÓN (una entrada humana = muchos comandos)  
**Propósito**: Narrative - qué hice, por qué, con qué éxito

---

## ❌ EL PROBLEMA FUNDAMENTAL

**Telemetry registra:**
- `ctx.search` ejecutado a las 19:17:00 (14ms, 0 hits)
- `lsp.spawn` ejecutado a las 19:17:00 (1ms, pid=16994)
- `ctx.sync` ejecutado a las 19:34:38 (450ms, ok)

**Session necesita:**
- "Investigué por qué LSP daemon tenía lifecycle issues. Usé lsp_daemon.py y lsp_client.py. Fixed threading bug. Tests passing."

**SON NIVELES DE ABSTRACCIÓN DIFERENTES.**

Telemetry es **log de sistema** (máquina).  
Session es **bitácora de trabajo** (humano).

---

## 🔴 PROBLEMA #1: Impedance Mismatch

**Pregunta**: ¿Cómo agregas 50 eventos de telemetry en UNA entrada de session?

**Ejemplo real del JSONL**:
```
19:17:00 - lsp.spawn
19:17:00 - lsp.state_change
19:17:00 - lsp.daemon_status
19:17:00 - lsp.request (hover)
19:17:00 - lsp.request (hover)
19:17:03 - lsp.daemon_status
19:17:03 - lsp.request (hover)
```

¿Esto es UN task o SIETE? Telemetry no tiene concepto de "sesión de trabajo".

**NECESITARÍAS**:
- Agregar campo `session_id` a cada evento de telemetry
- Script que agrupe eventos por `session_id`
- Lógica para detectar cuándo termina una sesión

**COSTO**: Añades complejidad masiva al sistema de telemetry que NO necesita.

---

## 🔴 PROBLEMA #2: Propósito Conflictivo

**Telemetry está diseñado para**:
- Performance profiling (timing_ms)
- Error tracking (warnings, result.status)
- Debugging de infraestructura (¿por qué LSP falló?)

**Session está diseñado para**:
- Onboarding de agentes ("¿qué hizo el agente anterior?")
- Context recall ("¿en qué archivos trabajamos en debug?")
- Decision tracking ("¿por qué elegimos approach X?")

**Si mezclas ambos**:
- Telemetry se contamina con datos narrative que no son métricas
- Session pierde claridad al mezclarse con ruido de infraestructura

---

## 🔴 PROBLEMA #3: Privacidad y Redacción

**Telemetry policy** (líneas 159-166):
> "Paths: Always use `_relpath` to log relative paths. NEVER log absolute paths."  
> "Segment: Log `segment_id` (SHA-256 hash prefix), not `segment_path`."

**Session necesita**:
- Paths legibles de archivos touched (ej: `src/infrastructure/lsp_client.py`)
- Summary texto libre del agente (puede contener info sensible)

**CONTRADICCIÓN**:
- Telemetry está hardened para NO leakear PII
- Session NECESITA info legible (paths, summaries)

**Si extiendes telemetry**: ¿Relajas las reglas de redacción? Eso degrada la seguridad.

---

## 🟡 PROBLEMA #4: Schema Pollution

**Telemetry tiene 9 campos top-level**:
```
ts, run_id, segment_id, cmd, args, result, timing_ms, warnings, x
```

**Session necesitaría añadir**:
```
task_type, summary, files_touched, tools_used, outcome, tags
```

**Opciones**:
1. **Top-level** → Rompe el schema estable de telemetry
2. **Bajo `x` namespace** → Session data queda como "extra", no first-class

**Ninguna opción es limpia.**

---

## 🟢 LA ÚNICA FORMA EN QUE FUNCIONA

**Opción Híbrida**:
1. Telemetry sigue siendo telemetry (no cambios)
2. NUEVO evento tipo `session.entry` que SE REGISTRA en telemetry JSONL
3. Session.md se genera DESDE filtrar `cmd == "session.entry"` del telemetry JSONL

**Schema**:
```json
{
  "ts": "2026-01-04T09:50:21-03:00",
  "run_id": "run_X",
  "segment_id": "abc123",
  "cmd": "session.entry",
  "args": {"summary": "Fixed bug", "files": ["a.py"], "type": "debug"},
  "result": {"outcome": "success"},
  "timing_ms": 0,
  "warnings": [],
  "x": {"tags": ["lsp", "daemon"]}
}
```

**VENTAJAS**:
- ✅ Un solo archivo JSONL (telemetry)
- ✅ Session entries son events más de telemetry
- ✅ Telemetry schema no se contamina (es solo otro `cmd`)

**DESVENTAJAS**:
- ⚠️ Session entries mezcladas con ruido de lsp.spawn, ctx.sync, etc.
- ⚠️ Query `session.entry` requiere filtrar TODO el JSONL
- ⚠️ Telemetry crece más rápido (session + metrics)

---

## 🎯 VEREDICTO BRUTAL

**TU PREGUNTA**: "¿Solo tendríamos que modificarlo para que tenga lo que necesita trifecta?"

**MI RESPUESTA**: **NO ES TAN SIMPLE**.

Extender telemetry tiene **4 problemas críticos** que no son triviales:
1. Impedance mismatch (eventos vs sesiones)
2. Propósito conflictivo (metrics vs narrative)
3. Privacidad contradictoria (redaction vs readability)
4. Schema pollution (9 campos + 6 nuevos)

**LA OPCIÓN HÍBRIDA** (session.entry como event type) funciona, pero:
- ⚠️ Mezcla session con ruido de infraestructura
- ⚠️ Requiere filtrado en cada query
- ⚠️ No es semánticamente limpio

---

## 🤔 LA PREGUNTA CORRECTA

**No es**: "¿Podemos usar telemetry?"  
**Es**: "¿DEBERÍAMOS usar telemetry?"

**Trade-off**:
- **Opción A**: Extender telemetry → Un solo JSONL, pero semánticamente sucio
- **Opción B**: Session JSONL separado → Dos archivos, pero semánticamente limpio

**Mi recomendación escéptica**:
Si el overlap fuera 95%, diría "usa telemetry".  
Pero el overlap es de granularidad (task vs comando), no de datos.  
Son **propósitos diferentes** con **niveles de abstracción diferentes**.

**Necesito que respondas**:
1. ¿Session entries van en el prompt del agente (alto valor) o solo son para query (bajo valor)?
2. ¿Tolerarías que session search traiga ruido de lsp.spawn, ctx.sync?
3. ¿El costo de DOS archivos JSONL realmente te duele, o es acceptable?

**NO implementes hasta responder estas 3.**
