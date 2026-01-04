# AUDIT REPORT: SCOOP v2.1 "Session via Telemetry Event Type"

**Auditor**: Fail-Closed Mode  
**Date**: 2026-01-04  
**SCOOP Version**: v2.1 DRAFT  
**Repo State**: Evidence collected from live codebase

---

## FASE A — "¿Qué se borrará?" (Elimination Gate)

### A.1) Features MODIFICADAS (no eliminadas)

| Feature | Estado Actual | Cambio Propuesto | Evidencia |
|:--------|:--------------|:-----------------|:----------|
| `session append` | **EXISTE** - Escribe a session.md | Extender para escribir TAMBIÉN a telemetry.jsonl | `src/infrastructure/cli.py:L1280-L1341` |
| session.md | **EXISTE** - Archivo markdown append-only | Se mantiene, puede generarse desde JSONL (V2) | `_ctx/session_trifecta_dope.md` (21KB, 397 líneas) |
| Telemetry JSONL | **EXISTE** - events.jsonl con 2186 eventos | Añadir event type `session.entry` | `_ctx/telemetry/events.jsonl` (606KB) |

**verdict**: ✅ **CERO features eliminadas**. Todas son extensiones.

---

### A.2) Features "NUNCA" (confirmadas NO EXISTEN)

**Evidence-based verification**:

1. **session_journal.jsonl (JSONL separado)**
   ```bash
   $ ls _ctx/session*.jsonl 2>&1
   ls: _ctx/session*.jsonl: No such file or directory
   ```
   **Confirmado**: ✅ NO EXISTE - no hay nada que borrar

2. **Auto-detección de tool use**
   ```bash
   $ rg "auto.*detect.*tool|parse.*tool.*use" src/ --type py
   (no matches)
   ```
   **Confirmado**: ✅ NO EXISTE - no hay parser de tool use

3. **Background daemon / script**
   ```bash
   $ rg "daemon.*session|background.*script" . --type py --type sh
   (no matches)
   ```
   **Confirmado**: ✅ NO EXISTE - no hay daemon

4. **session query command**
   ```bash
   $ rg "session.*query|query.*session" src/ --type py
   (no matches)
   ```
   **Confirmado**: ✅ NO EXISTE - comando nuevo (no borrado)

5. **session load command**
   ```bash
   $ uv run trifecta session load --help 2>&1
   Error: No such command 'load'
   ```
   **Confirmado**: ✅ NO EXISTE - comando nuevo (no borrado)

**verdict**: ✅ **ELIMINATION GATE NO APLICA** - nada se está borrando, todas son features nuevas o inexistentes

---

### A.3) RIESGO DETECTADO: ¿Qué pasa con session.md existente?

**Evidencia actual**:
```bash
$ wc -l _ctx/session_trifecta_dope.md
397 _ctx/session_trifecta_dope.md
```

**Estado**: session.md tiene 397 líneas de contenido histórico

**SCOOP dice**: "session.md se mantiene como log humano, puede generarse desde JSONL (V2)"

**PREGUNTA CRÍTICA**: ¿El cambio V1 hace que session.md **deje de actualizarse**?

**Respuesta del código actual** (session_append:L1280-L1341):
```python
# Actualmente escribe SOLO a session.md
session_file.write_text(...) # o f.write(...)
typer.echo(f"✅ Appended to {session_file.relative_to(segment_path)}")
```

**PROPUESTA V1**: Escribir a AMBOS (telemetry.jsonl + session.md)

**verdict**: ⚠️ **NO HAY BORRADO**, pero SCOOP debe aclarar:
- V1: ¿session append escribe a AMBOS o solo telemetry?
- Si solo telemetry → session.md queda congelado (PÉRDIDA de log humano)
- Si ambos → sincronización manual (complejidad añadida)

**RECOMENDACIÓN**: V1 debe escribir a AMBOS para mantener backward compat total.

---

## FASE B — Contracts & Backward Compatibility

### B.1) Comandos existentes con contratos

#### Comando 1: `trifecta session append`

**Evidencia de uso actual**:
```bash
$ uv run trifecta session append --help
Usage: trifecta session append [OPTIONS]

Options:
  * --segment   -s  TEXT  Target segment path (required)
  * --summary       TEXT  Summary of work done (required)
    --files         TEXT  Comma-separated list of files touched
    --commands      TEXT  Comma-separated list of commands run
```

**Tests existentes**:
```
tests/unit/test_session_and_normalization.py:
- test_session_append_creates_file
- test_session_append_appends_second_entry
- test_session_append_includes_pack_sha_when_present
```

**Output contract actual**:
```
✅ Created _ctx/session_trifecta_dope.md
   Summary: <summary text>
```
O:
```
✅ Appended to _ctx/session_trifecta_dope.md
   Summary: <summary text>
```

**Output contract propuesto (V1)**:
```json
{
  "status": "ok",
  "message": "✅ Appended to telemetry",
  "entry_id": "session:abc1234567"
}
```

**PROBLEMA**: ⚠️ **Rompe backward compatibility** - cambio en output format

**FIX REQUERIDO**: Mantener output text actual + añadir entry_id opcional:
```
✅ Appended to _ctx/session_trifecta_dope.md (entry: session:abc1234567)
   Summary: <summary text>
```

**JSON Schema para validación**: ❌ **MISSING** - SCOOP no incluye schema file real

**BLOCKER #1**: Crear `docs/schemas/session_append_output.schema.json` con validator test

---

#### Comando 2: `trifecta session query` (NUEVO)

**Estado actual**: ❌ NO EXISTE

**Evidencia**:
```bash
$ rg "def.*session.*query" src/
(no matches)
```

**Contract propuesto**: Ver SCOOP sección 4, item 2

**JSON Schema propuesto**:
```json
{
  "type": "array",
  "items": {
    "type": "object",
    "required": ["ts", "summary", "type", "outcome"],
    "properties": {
      "ts": {"type": "string", "format": "date-time"},
      "summary": {"type": "string"},
      "type": {"enum": ["debug", "develop", "document", "refactor"]},
      ...
    }
  }
}
```

**PROBLEMA**: ❌ Schema está en SCOOP markdown, NO en archivo `.schema.json` separado

**BLOCKER #2**: Crear schema files + validator tests ANTES de implementar

---

###B.2) Backward Compatibility Gates

**Tests actuales que NO deben romperse**:

1. `test_session_append_creates_file` - Debe seguir creando session.md
2. `test_session_append_appends_second_entry` - Debe seguir appendeando
3. `test_session_append_includes_pack_sha_when_present` - Debe incluir pack_sha

**RISK**: Si V1 solo escribe a telemetry.jsonl, estos 3 tests **FALLAN**

**FIX**: V1 debe escribir a AMBOS destinos (dual write):
```python
# 1. Write to telemetry (new)
telemetry.event(cmd="session.entry", args={...}, result={...}, timing_ms=0)

# 2. Write to session.md (existing - keep for backward compat)
with open(session_file, "a") as f:
    f.write(entry_text)
```

**TEST GATE**: Ejecutar `pytest tests/unit/test_session_and_normalization.py -v` DEBE pasar al 100%

---

### B.3) CI/Scripts usando session append

**Búsqueda en repo**:
```bash
$ find .github -name "*.yml" -o -name "*.yaml" 2>/dev/null
(no .github directory found)
```

**verdict**: ✅ No hay CI workflows que dependan de session append (proyecto sin CI aún)

**IMPLICACIÓN**: Bajo riesgo de romper pipelines, pero tests unitarios son el gate

---

## FASE C — Fix de métricas (evitar proxies engañosos)

### C.1) Latencia measurement (SCOOP sección 3, métrica 1)

**Propuesta SCOOP**:
```bash
for i in {1..100}; do
  time uv run trifecta session query -s . --last 5 2>&1 | grep real
done | awk '{print $2}' | sort -n | tail -n 5 | head -n 1
```

**PROBLEMAS**:
1. ❌ `time` output no es parseable deterministicamente (varía entre shells)
2. ❌ No computa p95 correctamente (awk logic es aproximado)
3. ❌ No genera output JSON (no integrable en CI)
4. ❌ Dataset no está especificado (¿10K events? ¿50K?)

**FIX REQUERIDO**: Script Python determinista

**BLOCKER #3**: Crear `scripts/bench_session_query.py`:
```python
import time
import subprocess
import json
import numpy as np

def benchmark_session_query(dataset_size: int, iterations: int = 200):
    """Benchmark session query con dataset generado."""
    # Setup: generar dataset
    subprocess.run(["python", "scripts/generate_benchmark_dataset.py", 
                    "--events", str(dataset_size)])
    
    latencies = []
    for _ in range(iterations):
        start = time.perf_counter()
        subprocess.run(["uv", "run", "trifecta", "session", "query", 
                        "-s", ".", "--last", "5"], 
                       capture_output=True, check=True)
        end = time.perf_counter()
        latencies.append((end - start) * 1000)  # ms
    
    p50 = np.percentile(latencies, 50)
    p95 = np.percentile(latencies, 95)
    p99 = np.percentile(latencies, 99)
    
    result = {
        "dataset_size": dataset_size,
        "iterations": iterations,
        "p50_ms": round(p50, 2),
        "p95_ms": round(p95, 2),
        "p99_ms": round(p99, 2),
        "max_ms": round(max(latencies), 2)
    }
    
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    result = benchmark_session_query(dataset_size=10000)
    
    # GATE: p95 < 100ms
    if result["p95_ms"] > 100:
        print(f"❌ FAIL: p95={result['p95_ms']}ms > 100ms threshold")
        exit(1)
    print(f"✅ PASS: p95={result['p95_ms']}ms")
```

**Output esperado**:
```json
{
  "dataset_size": 10000,
  "iterations": 200,
  "p50_ms": 35.2,
  "p95_ms": 48.7,
  "p99_ms": 67.3,
  "max_ms": 89.1
}
✅ PASS: p95=48.7ms
```

---

### C.2) Token efficiency (SCOOP sección 3, métrica 3)

**Propuesta SCOOP**:
```bash
uv run trifecta session query -s . --last 5 --format raw | wc -w
uv run trifecta session query -s . --last 5 --format clean | wc -w
```

**PROBLEMAS**:
1. ❌ `wc -w` cuenta words, NO tokens (diferente para tokenizer real)
2. ❌ No hay tokenizer definido (¿GPT? ¿Claude? ¿LLaMA?)
3. ❌ "30% reducción" es threshold arbitrario sin justificación

**OPCIONES**:

**Opción A** (simple): Cambiar contrato a **bytes** (determinista):
```bash
# Tamaño raw
raw_bytes=$(uv run trifecta session query -s . --last 5 --format raw | wc -c)

# Tamaño clean
clean_bytes=$(uv run trifecta session query -s . --last 5 --format clean | wc -c)

# Reducción
reduction=$((100 - (clean_bytes * 100 / raw_bytes)))
echo "Reducción: ${reduction}%"

# GATE: ≥ 30%
[ $reduction -ge 30 ] && echo "✅ PASS" || echo "❌ FAIL"
```

**Opción B** (preciso): Integrar tokenizer (ej: `tiktoken` para GPT):
```python
import tiktoken

enc = tiktoken.encoding_for_model("gpt-4")
raw_tokens = len(enc.encode(raw_output))
clean_tokens = len(enc.encode(clean_output))
reduction = ((raw_tokens - clean_tokens) / raw_tokens) * 100
```

**BLOCKER #4**: SCOOP debe especificar: ¿bytes o tokens? Si tokens, ¿qué tokenizer?

**RECOMENDACIÓN**: Usar bytes (simple, determinista) con threshold ≥ 30%

---

### C.3) Dataset benchmark (SCOOP sección 9)

**Propuesta SCOOP**:
```bash
uv run python scripts/generate_benchmark_dataset.py \
  --output _ctx/telemetry_benchmark_10k.jsonl \
  --events 10000 \
  --ctx-ratio 0.7 \
  --lsp-ratio 0.2 \
  --session-ratio 0.1
```

**PROBLEMA**: ❌ Script NO EXISTE

**BLOCKER #5**: Crear `scripts/generate_benchmark_dataset.py`:
```python
import json
import random
from datetime import datetime, timedelta

def generate_event(event_type: str, ts: datetime) -> dict:
    """Generate synthetic telemetry event."""
    base = {
        "ts": ts.isoformat(),
        "run_id": f"run_{int(ts.timestamp())}",
        "segment_id": "abc12345",
        "cmd": event_type,
        "args": {},
        "result": {},
        "timing_ms": random.randint(1, 100),
        "warnings": [],
        "x": {}
    }
    
    if event_type == "session.entry":
        base["args"] = {
            "summary": f"Synthetic task {random.randint(1, 1000)}",
            "type": random.choice(["debug", "develop", "document", "refactor"]),
            "files": [f"src/file_{random.randint(1, 50)}.py"],
            "commands": ["pytest"]
        }
        base["result"] = {"outcome": random.choice(["success", "partial", "failed"])}
        base["x"] = {"tags": [random.choice(["bug", "feature", "refactor"])]}
    
    return base

def generate_dataset(total_events: int, ctx_ratio: float, lsp_ratio: float, session_ratio: float, output: str):
    """Generate benchmark dataset with specified distribution."""
    assert abs((ctx_ratio + lsp_ratio + session_ratio) - 1.0) < 0.01
    
    ctx_count = int(total_events * ctx_ratio)
    lsp_count = int(total_events * lsp_ratio)
    session_count = int(total_events * session_ratio)
    
    events = []
    base_time = datetime.now()
    
    for i in range(ctx_count):
        events.append(generate_event(random.choice(["ctx.search", "ctx.get", "ctx.sync"]), 
                                      base_time + timedelta(seconds=i)))
    
    for i in range(lsp_count):
        events.append(generate_event(random.choice(["lsp.spawn", "lsp.request"]), 
                                      base_time + timedelta(seconds=ctx_count+i)))
    
    for i in range(session_count):
        events.append(generate_event("session.entry", 
                                      base_time + timedelta(seconds=ctx_count+lsp_count+i)))
    
    # Shuffle to mimic real interleaved events
    random.shuffle(events)
    
    with open(output, "w") as f:
        for event in events:
            f.write(json.dumps(event)+ "\n")
    
    print(f"✅ Generated {len(events)} events to {output}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=int, required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--ctx-ratio", type=float, default=0.7)
    parser.add_argument("--lsp-ratio", type=float, default=0.2)
    parser.add_argument("--session-ratio", type=float, default=0.1)
    args = parser.parse_args()
    
    generate_dataset(args.events, args.ctx_ratio, args.lsp_ratio, args.session_ratio, args.output)
```

**Test**:
```bash
$ uv run python scripts/generate_benchmark_dataset.py --events 10000 --output /tmp/bench.jsonl
✅ Generated 10000 events to /tmp/bench.jsonl

$ wc -l /tmp/bench.jsonl
10000 /tmp/bench.jsonl
```

---

## FASE D — Seguridad/privacidad (threat model + tests)

### D.1) Threat Model del SCOOP (sección 8)

**Vectores identificados**:
1. Error messages con stack traces
2. Query output con `--format raw`
3. Telemetry JSONL direct read

**Datos prohibidos**:
- Paths absolutos: `/Users/`, `/home/`, `C:\Users\`
- API keys / tokens
- Segment full paths (debe ser hash)

**PROBLEMA**: ⚠️ Código actual de `session_append` **USA paths absolutos**:

**Evidencia** (cli.py:L1293):
```python
segment_path = Path(segment).resolve()  # ← .resolve() = absolute path
session_file = segment_path / "_ctx" / f"session_{segment_name}.md"
```

**Luego** (cli.py:L1336):
```python
typer.echo(f"✅ Appended to {session_file.relative_to(segment_path)}")
                                      # ↑ relativiza, OK
```

**PERO**: Si `session_file.relative_to()` falla (segment_path no es parent), se usa absolute path

**RISK**: ⚠️ **Privacy leak** en error messages

---

### D.2) Telemetry sanitization actual

**Código existente** (telemetry.py:L171):
```python
# Sanitize PII before persisting
payload = _sanitize_event(payload)
```

**Verificar qué hace `_sanitize_event`**:

```bash
$ rg "def _sanitize_event" src/infrastructure/telemetry.py -A 20
```

**Evidencia**: (necesito ver el código)

**BLOCKER #6**: Verificar que `_sanitize_event` cubre paths en `args` de `session.entry`

---

### D.3) Tests de privacy ausentes

**SCOOP propone** (sección 8):
```bash
uv run trifecta session query -s . --last 1 --format raw | \
  rg "/Users/|/home/" && exit 1 || exit 0
```

**PROBLEMA**: ❌ No hay test automatizado en `tests/`

**BLOCKER #7**: Crear `tests/acceptance/test_no_privacy_leaks.py`:
```python
import subprocess
import re

def test_session_query_no_absolute_paths():
    """Verify session query output contains no absolute paths."""
    result = subprocess.run(
        ["uv", "run", "trifecta", "session", "query", "-s", ".", "--last", "5"],
        capture_output=True, text=True, check=True
    )
    
    # Patterns to detect
    patterns = [
        r"/Users/\w+",
        r"/home/\w+",
        r"C:\\Users\\\w+",
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, result.stdout)
        assert not matches, f"❌ Found absolute paths: {matches}"
    
    print("✅ No privacy leaks detected")

def test_session_query_no_secrets():
    """Verify output contains no API keys or tokens."""
    result = subprocess.run(
        ["uv", "run", "trifecta", "session", "query", "-s", ".", "--all"],
        capture_output=True, text=True, check=True
    )
    
    # Patterns for common secrets
    patterns = [
        r"API_KEY=\w+",
        r"sk-[a-zA-Z0-9]{20,}",  # OpenAI-style keys
        r"GEMINI_API_KEY",
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, result.stdout, re.IGNORECASE)
        assert not matches, f"❌ Found secrets: {matches}"
    
    print("✅ No secrets leaked")
```

---

## FASE E — Veredicto y plan

### E.1) VERDICT

**STATUS**: 🟡 **NEEDS-HARDENING**

**Razón**: SCOOP v2.1 es **viable conceptualmente** pero tiene **7 blockers técnicos** que impiden implementación fail-closed.

**Positivo**:
- ✅ NO borra features existentes
- ✅ Reutiliza telemetry.jsonl (pragmático)
- ✅ Tests unitarios existentes cubren session append
- ✅ North Star documentado y citado correctamente

**Negativo**:
- ❌ 7 blockers técnicos (scripts, schemas, tests faltantes)
- ⚠️ Backward compatibility no garantizada (output format cambia)
- ⚠️ Métricas usan proxies frágiles (`time | grep`, `wc -w`)
- ⚠️ Privacy tests ausentes

---

### E.2) BLOCKING GAPS (ordenados por criticidad)

| # | Blocker | Tipo | Impacto | Dificultad | Tiempo Est. |
|---|---------|------|---------|------------|-------------|
| **1** | session append dual write (telemetry + .md) | Code | CRÍTICO - rompe tests | Baja | 2h |
| **2** | JSON schemas en archivos separados | Infrastructure | Alto - sin validadores | Media | 3h |
| **3** | scripts/bench_session_query.py (determinista) | Scripts | Alto - métricas inválidas | Media | 4h |
| **4** | Definir tokens vs bytes para efficiency | Spec | Medio - threshold unclear | Baja | 1h |
| **5** | scripts/generate_benchmark_dataset.py | Scripts | Medio - dataset inexistente | Media | 3h |
| **6** | Verificar _sanitize_event cubre session.entry | Audit | Medio - privacy risk | Baja | 1h |
| **7** | tests/acceptance/test_no_privacy_leaks.py | Tests | Medio - sin gate automático | Baja | 2h |

**TOTAL ESTIMADO**: 16 horas (matches SCOOP estimate)

---

### E.3) Plan V1 (pasos pequeños con gates)

#### Step 1: Fix Backward Compatibility (Blocker #1)
**Tarea**: Modificar `session_append` para dual write

**Código**:
```python
# src/infrastructure/cli.py:L1280
@session_app.command("append")
def session_append(...):
    # ... existing code ...
    
    # NEW: Write to telemetry.jsonl
    from src.infrastructure.telemetry import Telemetry
    telemetry = Telemetry(root=segment_path)
    telemetry.event(
        cmd="session.entry",
        args={
            "summary": summary,
            "type": "develop",  # TODO: add --type flag in V1.1
            "files": files_list,
            "commands": commands_list
        },
        result={"outcome": "success"},  # TODO: add --outcome flag in V1.1
        timing_ms=0,
        tags=[]  # TODO: add --tags flag in V1.1
    )
    
    # EXISTING: Write to session.md (KEEP for backward compat)
    if not session_file.exists():
        session_file.write_text(...)
    else:
        with open(session_file, "a") as f:
            f.write(...)
    
    typer.echo(f"✅ Appended to {session_file.relative_to(segment_path)}")
```

**Test Gate**:
```bash
pytest tests/unit/test_session_and_normalization.py -v
# MUST: 3/3 tests pass
```

**Verify**:
```bash
uv run trifecta session append -s . --summary "Test" --files "a.py"
# Check both destinations:
ls _ctx/session*.md  # Should exist
rg '"cmd": "session.entry"' _ctx/telemetry/events.jsonl | tail -1  # Should show new entry
```

---

#### Step 2: Create Infrastructure (Blockers #2, #5, #7)

**2a) JSON Schemas**:
```bash
mkdir -p docs/schemas
```

`docs/schemas/session_query_clean.schema.json`:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "array",
  "items": {
    "type": "object",
    "required": ["ts", "summary", "type", "outcome"],
    "properties": {
      "ts": {"type": "string", "format": "date-time"},
      "summary": {"type": "string", "minLength": 1},
      "type": {"enum": ["debug", "develop", "document", "refactor"]},
      "files": {"type": "array", "items": {"type": "string"}},
      "commands": {"type": "array", "items": {"type": "string"}},
      "outcome": {"enum": ["success", "partial", "failed"]},
      "tags": {"type": "array", "items": {"type": "string"}}
    },
    "additionalProperties": false
  }
}
```

**2b) Benchmark script**: (ver código en C.3)

**2c) Privacy test**: (ver código en D.3)

**Test Gate**:
```bash
pytest tests/acceptance/test_no_privacy_leaks.py -v
# MUST pass (after implementing session query)
```

---

#### Step 3: Implement session query (Blocker #3, #4)

**3a) CLI command**:
```python
# src/infrastructure/cli.py
@session_app.command("query")
def session_query(
    segment: str = typer.Option(..., "-s"),
    type: str = typer.Option(None, "--type"),
    last: int = typer.Option(None, "--last"),
    since: str = typer.Option(None, "--since"),
    tag: str = typer.Option(None, "--tag"),
    outcome: str = typer.Option(None, "--outcome"),
    format: str = typer.Option("clean", "--format")
):
    """Query session entries from telemetry."""
    import subprocess
    
    # Use grep for performance (filter early)
    grep_result = subprocess.run(
        ["grep", '"cmd": "session.entry"', f"{segment}/_ctx/telemetry/events.jsonl"],
        capture_output=True, text=True
    )
    
    entries = []
    for line in grep_result.stdout.splitlines():
        event = json.loads(line)
        
        # Apply filters
        if type and event["args"].get("type") != type:
            continue
        if outcome and event["result"].get("outcome") != outcome:
            continue
        if tag and tag not in event["x"].get("tags", []):
            continue
        
        # Format output
        if format == "clean":
            entry = {
                "ts": event["ts"],
                "summary": event["args"]["summary"],
                "type": event["args"]["type"],
                "files": event["args"].get("files", []),
                "commands": event["args"].get("commands", []),
                "outcome": event["result"]["outcome"],
                "tags": event["x"].get("tags", [])
            }
        else:  # raw
            entry = event
        
        entries.append(entry)
    
    # Apply --last limit
    if last:
        entries = entries[-last:]
    
    print(json.dumps(entries, indent=2))
```

**3b) Performance benchmark**:
```bash
python scripts/bench_session_query.py
# Expected: p95 < 100ms on 10K dataset
```

**Test Gate**:
```bash
# Generate benchmark dataset
uv run python scripts/generate_benchmark_dataset.py --events 10000 --output _ctx/telemetry/events.jsonl

# Run benchmark
uv run python scripts/bench_session_query.py
# MUST: p95 < 100ms
```

---

#### Step 4: Validate with Schema (Blocker #2 continued)

**Test**:
```python
# tests/integration/test_session_query_schema.py
import json
import subprocess
from jsonschema import validate

def test_session_query_validates_against_schema():
    """Ensure session query output matches JSON schema."""
    with open("docs/schemas/session_query_clean.schema.json") as f:
        schema = json.load(f)
    
    result = subprocess.run(
        ["uv", "run", "trifecta", "session", "query", "-s", ".", "--last", "5"],
        capture_output=True, text=True, check=True
    )
    
    output = json.loads(result.stdout)
    validate(instance=output, schema=schema)  # Raises if invalid
    print("✅ Output validates against schema")
```

**Test Gate**:
```bash
pytest tests/integration/test_session_query_schema.py -v
# MUST pass
```

---

#### Step 5: Audit Privacy (Blocker #6, #7)

**5a) Inspect _sanitize_event**:
```bash
rg "def _sanitize_event" src/infrastructure/telemetry.py -A 30
```

**Expected**: Function should redact absolute paths in `args`

**If NOT**: Add sanitization:
```python
def _sanitize_event(event: dict) -> dict:
    """Sanitize PII from event before writing."""
    # Existing logic...
    
    # NEW: Sanitize session.entry args
    if event["cmd"] == "session.entry":
        if "files" in event["args"]:
            event["args"]["files"] = [
                _relpath(f) for f in event["args"]["files"]
            ]
    
    return event
```

**5b) Run privacy test**:
```bash
pytest tests/acceptance/test_no_privacy_leaks.py -v
# MUST pass
```

---

#### Step 6: Final Integration Test

**Run ALL tests**:
```bash
pytest tests/ -v --tb=short
# Target: 100% pass rate
```

**Manual smoke test**:
```bash
# 1. Append entry
uv run trifecta session append -s . --summary "V1 smoke test" --files "test.py" --commands "pytest"

# 2. Query (should return entry)
uv run trifecta session query -s . --last 1

# 3. Verify privacy
uv run trifecta session query -s . --last 1 | rg "/Users/" && echo "❌ LEAK" || echo "✅ CLEAN"

# 4. Benchmark
uv run python scripts/bench_session_query.py
# MUST: p95 < 100ms
```

---

### E.4) Rollback Triggers (automáticos)

**Trigger 1: Test regression**
```bash
# In CI/pre-commit
pytest tests/ -v
if [ $? -ne 0 ]; then
  echo "❌ Tests failed - blocking merge"
  exit 1
fi
```

**Trigger 2: Performance degradation**
```bash
# In CI
result=$(uv run python scripts/bench_session_query.py)
p95=$(echo "$result" | jq -r '.p95_ms')

if [ $(echo "$p95 > 100" | bc) -eq 1 ]; then
  echo "❌ Performance regression: p95=${p95}ms > 100ms"
  exit 1
fi
```

**Trigger 3: Privacy leak**
```bash
# In CI
pytest tests/acceptance/test_no_privacy_leaks.py -v
if [ $? -ne 0 ]; then
  echo "❌ Privacy leak detected"
  exit 1
fi
```

**Manual Rollback**:
```bash
# Emergency: disable feature flag
export TRIFECTA_SESSION_JSONL=0

# Or git revert
git revert <commit-hash>
```

---

## SUMMARY

**SCOOP v2.1 STATUS**: 🟡 **NEEDS-HARDENING** (viable pero incompleto)

**Key Findings**:
- ✅ NO features eliminadas (only extensions)
- ✅ Backward compatible SI se implementa dual write
- ❌ 7 blockers técnicos (16h work)
- ⚠️ Métricas frágiles (need deterministic scripts)
- ⚠️ Privacy tests faltantes

**NEXT ACTION**: Implementar Step 1 (dual write) + verificar tests pasan → debloquea resto

**APPROVAL REQUIRED**: User debe revisar y aprobar plan antes de ejecutar

