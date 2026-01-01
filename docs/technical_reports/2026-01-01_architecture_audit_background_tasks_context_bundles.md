---
title: "Auditoría de Arquitectura: Background Tasks & Context Bundles"
date: 2026-01-01
scope: Integration Opportunities Analysis
status: Architecture Review
auditor: GitHub Copilot (Agent Auditor)
version: 1.0
---

# Auditoría de Arquitectura: Background Tasks & Context Bundles para Trifecta

## EXECUTIVE SUMMARY (8–12 líneas)

Trifecta es un sistema CLI de "Programming Context Calling" (PCC) operacional en MVP, con arquitectura Clean Architecture establecida (domain/application/infrastructure), telemetría local-first, y Context Packs generativos. El presente análisis identifica **12 puntos de integración concretos** para incorporar dos conceptos: (1) **Background Tasks** (ejecución asíncrona de agentes/tareas largas con state tracking y report streaming) y (2) **Context Bundles** (cajas negras auditables que empaquetan: prompt inicial, tool calls ejecutados, contexto leído, eventos LSP/AST, policies de filtrado, y manifest versionado).

**Hallazgo crítico**: El pipeline actual tiene **3 riesgos split-brain** (telemetry.py flock, context_pack.json sin lock, session.md append sin coordinator), **2 bloat vectors** (node_modules y .git pueden ser capturados por bundles si no hay denylist estricta), y **cero instrumentación para tool-call recording** (no hay hooks entre CLI → UseCase → FileSystem).

**Recomendaciones priorizadas**:
1. **MVP-1 (Bundle Recorder)**: Agregar `ContextBundleRecorder` a CLI como wrapper de telemetry, capturando stdin/stdout + tool_calls + file_reads (week 1, low-risk).
2. **MVP-2 (Background Runner)**: Implementar `BackgroundTaskManager` con state machine (running/done/failed) y lockfile en `_ctx/tasks/` (week 2, med-risk por concurrency).
3. **MVP-3 (LSP Events)**: Instrumentar AST/LSP events como opcionales en bundles, con feature-flag y fallback-ready (week 4, high-risk por external dependency).

---

## 1. MAPA DEL PIPELINE ACTUAL

### 1.1 Diagrama ASCII del Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│  TRIFECTA PIPELINE (MVP Operacional)                                    │
└─────────────────────────────────────────────────────────────────────────┘

ENTRADAS                    PROCESOS                    ARTEFACTOS EN DISCO
═══════════════════════════════════════════════════════════════════════════

CLI Args                    ┌─────────────────┐          _ctx/
  --segment PATH     ───────>│  CLI Router     │            ├── context_pack.json  [RW: BuildUseCase]
  --query "term"             │  (cli.py)       │            ├── session_*.md        [APPEND: session cmd]
  --task "desc"              └────────┬────────┘            ├── prime_*.md          [R: BuildUseCase]
                                      │                     ├── agent.md            [R: LoadUseCase]
                                      v                     ├── aliases.yaml        [R: SearchUseCase]
                          ┌─────────────────────┐          └── telemetry/
                          │  Use Cases Layer    │                ├── events.jsonl  [APPEND: Telemetry]
                          │  (application/)     │                ├── metrics.json  [RW: Telemetry.flush]
                          ├─────────────────────┤                └── last_run.json [W: Telemetry.flush]
                          │ • BuildContextPack  │
                          │ • SearchUseCase     │          Locks/Ownership:
                          │ • GetChunkUseCase   │          ──────────────────
                          │ • SyncContext       │          • events.jsonl:  fcntl.LOCK_EX (telemetry.py:191)
                          │ • MacroLoad         │                           [SKIP write if busy]
                          │ • SessionAppend     │          • context_pack.json: NO LOCK (¡RIESGO!)
                          └────────┬────────────┘          • session_*.md:   AtomicWriter (NO LOCK)
                                   │                       • metrics.json:    Single writer (flush)
                                   v
                    ┌──────────────────────────┐
                    │  Infrastructure Layer    │
                    │  (infrastructure/)       │
                    ├──────────────────────────┤
                    │ • FileSystemAdapter      │  ─────> Disk I/O (read/write/scan)
                    │ • Telemetry              │  ─────> _ctx/telemetry/* (flock)
                    │ • TemplateRenderer       │  ─────> Generación MD templates
                    │ • ContextService         │  ─────> JSON load context_pack
                    │ • AliasLoader             │  ─────> YAML parse aliases
                    └──────────────────────────┘

                    I/O per Stage:
                    ═══════════════════════════════════════════════════════
                    Stage               Input                 Output
                    ─────────────────────────────────────────────────────
                    ctx build           skill/prime/agent     context_pack.json (7 chunks)
                    ctx search          query + aliases       SearchResult (hits list)
                    ctx get             chunk IDs + mode      GetResult (text chunks)
                    ctx sync            segment path          rebuilt pack + validation
                    ctx validate        context_pack.json     ValidationResult (PASS/FAIL)
                    load                task + search query   MacroLoadResult (files list)
                    session append      summary + files       session_*.md (append entry)

                    Herramientas Clave:
                    ═══════════════════════════════════════════════════════
                    Comando                  Módulo                   Tool Impl
                    ──────────────────────────────────────────────────────────
                    trifecta ctx build       use_cases.py             BuildContextPackUseCase
                    trifecta ctx search      search_get_usecases.py   SearchUseCase → ContextService
                    trifecta ctx get         search_get_usecases.py   GetChunkUseCase → ContextService
                    trifecta load            use_cases.py             MacroLoadUseCase (Plan A/B)
                    trifecta session append  use_cases.py             SessionAppendUseCase
                    trifecta ctx stats       cli.py (direct)          Telemetry JSON read
```

### 1.2 Ownership Matrix (Quién Escribe Qué)

| Artefacto | Writer(s) | Lock Strategy | Risk |
|-----------|-----------|---------------|------|
| `_ctx/context_pack.json` | BuildContextPackUseCase (solo) | **NONE** ⚠️ | Split-brain si 2 builds concurrentes |
| `_ctx/session_*.md` | SessionAppendUseCase (append) | AtomicWriter (temp+rename) | Race condition en append sin coordinator |
| `_ctx/telemetry/events.jsonl` | Telemetry.event (multi-caller) | fcntl.LOCK_EX + LOCK_NB (skip if busy) | Log loss acceptable (design choice) |
| `_ctx/telemetry/metrics.json` | Telemetry.flush (once per run) | Single-writer (no concurrent runs expected) | Safe for MVP |
| `_ctx/telemetry/last_run.json` | Telemetry.flush | Overwrite-safe (single writer) | Safe |
| `skill.md`, `prime_*.md`, `agent.md` | Human/Agent edits (infrequent) | **NONE** | Assumed low contention |
| `_ctx/aliases.yaml` | AliasLoader (read-only in code) | N/A | Safe (read-only) |

**RIESGO CRÍTICO DETECTADO**:  
`context_pack.json` puede ser corrompido por `trifecta ctx build` concurrente (ej: 2 agentes corriendo `build` en paralelo). NO hay lock ni versioning.

---

## 2. MATRIZ "OPPORTUNITY MAP" (8+ Oportunidades)

| # | Punto del Pipeline | Concepto | Beneficio | Riesgo | Cambios | Dependencias | Métrica Validación |
|---|-------------------|----------|-----------|--------|---------|--------------|-------------------|
| **O1** | `cli.py` → UseCase wrappers | **Bundle** | Capturar prompt + args de cada comando CLI para replay | Log bloat si no hay rotation policy | MIN: Agregar `BundleRecorder.start_session()` al inicio de cada comando | Manifest schema v1 | `bundle_replay_success_rate` |
| **O2** | `Telemetry.event()` → events.jsonl | **Bundle** | Re-usar eventos existentes como parte del bundle (tool_calls timeline) | Eventos actuales no tienen `tool_call_id` ni `parent_id` para grafo | MID: Extender event schema con `tool_call_id`, `parent_trace_id`, `execution_order` | Refactor Telemetry event signature | `bundle_event_completeness` (% eventos con tool_call_id) |
| **O3** | `ContextService.search()` | **Bundle** | Grabar query + hits + scores como "search tool call" para bundle | Sin instrumentación actual de "qué chunk fue efectivamente útil" | MIN: Wrapper que loggea `search_request` + `search_response` a bundle events | ContextBundleRecorder | `search_tool_call_count` |
| **O4** | `ContextService.get()` | **Bundle** | Grabar IDs solicitados + modo + texto entregado (con redaction rules) | Texto completo puede explotar bundle size (MBs) | HIGH: Implementar redaction policy (PII, secrets, límite chars) | Policy YAML schema + redactor | `bundle_size_p95_mb`, `redaction_trigger_count` |
| **O5** | `MacroLoadUseCase` (Plan A/B fallback) | **Background** | Ejecutar Plan B (scan full workspace) en background mientras agente continúa con Plan A parcial | Fallback silencioso puede dejar task zombie | MID: Wrapper que forkea background task si Plan A tiene <3 hits | BackgroundTaskManager | `fallback_background_success_rate` |
| **O6** | `SessionAppendUseCase` | **Bundle** | Cada append de session.md puede ser un snapshot bundleable (mini-checkpoint) | Append-only log sin boundary markers hace difícil extraer "runs" | MIN: Agregar `## [BUNDLE_CHECKPOINT] run_id` marker antes de cada append | Session template update | `checkpoint_marker_count` |
| **O7** | `BuildContextPackUseCase` → AST parsing (future) | **Bundle** | Capturar AST request/response como eventos LSP en bundle (code symbols, definitions) | AST no implementado en v1, alta dependencia externa (pyright, tree-sitter) | HIGH: Feature flag `bundle.capture_ast_events`, con graceful degradation si LSP unavailable | LSP client library, AST parser | `ast_event_capture_rate`, `lsp_timeout_count` |
| **O8** | CLI command: `trifecta background start` | **Background** | Nueva familia de comandos para background task lifecycle (start/ps/tail/cancel) | Nuevo attack surface: task state en disco puede ser manipulado | HIGH: Implementar state machine en `_ctx/tasks/<task_id>/state.json` con versioned schema | BackgroundTaskManager + lockfile per task | `task_completion_rate`, `task_timeout_rate` |
| **O9** | `trifecta bundle pack` (new command) | **Bundle** | Comando que genera un `.trifecta-bundle.tar.gz` de último run (events + files + manifest) | Archive puede contener secrets si no hay scan previo | HIGH: Pre-scan con allowlist/denylist antes de pack | Bundle policy engine + secrets scanner | `bundle_pack_scan_failure_rate`, `secrets_detected_count` |
| **O10** | `trifecta bundle replay <bundle>` | **Bundle** | Replay de comandos desde un bundle (dry-run de tool calls para debug) | Replay puede tener side-effects si no se mockean writes | HIGH: Mockear FileSystemAdapter en replay mode, dry-run only | Replay engine con mocked I/O | `replay_fidelity_score` (% tool calls replayables) |
| **O11** | `FileSystemAdapter.scan_files()` | **Bundle** | Grabar lista de archivos escaneados (paths) como metadata del bundle | Scan puede capturar node_modules, .git (bloat) | MIN: Agregar exclusion patterns (GLOB) en bundle config | Denylist YAML | `scanned_paths_count`, `excluded_paths_count` |
| **O12** | `Telemetry.flush()` post-run | **Bundle** | Empaquetar telemetry completa como bundle footer (summary + SHA of all events) | Flush puede fallar silently (design actual: "never break app") | MID: Agregar bundle finalization step con retry + warning if flush fails | Bundle finalization hook | `bundle_finalization_success_rate` |

---

## 3. PROPUESTA MVP (3 Iteraciones)

### 3.1 Iteración 1: Bundle Recorder Mínimo (Week 1)

**Objetivo**: Capturar prompt + tool calls + file reads en un manifest auditable, sin modificar pipeline core.

#### 3.1.1 Definition of Done (DoD)

- [ ] Módulo `src/infrastructure/bundle_recorder.py` creado con:
  - `BundleRecorder.start_session(run_id, command, args)`
  - `BundleRecorder.log_tool_call(name, args, result, timing_ms)`
  - `BundleRecorder.log_file_read(path, lines_read, char_count)`
  - `BundleRecorder.finalize() -> Path` (genera manifest.json)
- [ ] Schema `bundle_manifest_v1.json` definido con campos mínimos:
  ```json
  {
    "schema_version": 1,
    "run_id": "run_1735772400",
    "created_at": "2026-01-01T12:00:00Z",
    "command": "trifecta ctx search",
    "args": {"query": "validate", "segment": ".", "limit": 5},
    "tool_calls": [
      {
        "id": "tc_001",
        "name": "ctx.search",
        "args": {"query": "validate"},
        "result": {"hits": 3},
        "timing_ms": 45,
        "timestamp": "2026-01-01T12:00:01Z"
      }
    ],
    "file_reads": [
      {"path": "_ctx/context_pack.json", "lines": [1, 156], "char_count": 28989}
    ],
    "sha256_digest": "abc123...",
    "policies_applied": "ctx_bundle_rules.yaml"
  }
  ```
- [ ] Policy file `_ctx/ctx_bundle_rules.yaml` con allowlist/denylist/limits:
  ```yaml
  schema_version: 1
  allow:
    - "*.md"
    - "_ctx/context_pack.json"
    - "_ctx/session_*.md"
  deny:
    - "node_modules/**"
    - ".git/**"
    - "**/*.pyc"
    - ".env"
    - "**/*secret*"
  limits:
    max_bundle_size_mb: 10
    max_file_reads: 100
    max_tool_calls: 50
  redaction:
    patterns:
      - 'api[_-]?key["\s:=]+[\w-]{20,}'
      - 'password["\s:=]+[^\s"]+'
  ```
- [ ] CLI wrapper en `cli.py`: Inicializar `BundleRecorder` al inicio de cada comando si `--bundle-capture` flag está presente.
- [ ] Test: `tests/unit/test_bundle_recorder.py` con 10 tests (start, log_tool_call, finalize, policy violations).
- [ ] Comando CLI: `trifecta bundle show <run_id>` para inspeccionar manifest (read-only).

#### 3.1.2 Tests Required

| Test | Assertion | Coverage |
|------|-----------|----------|
| `test_bundle_recorder_start_session` | `manifest.json` creado con run_id correcto | Happy path |
| `test_log_tool_call_with_redaction` | API key en result es redactado (`***`) | Redaction policy |
| `test_finalize_generates_sha256` | SHA256 digest matches computed hash | Integrity |
| `test_policy_deny_node_modules` | File read de `node_modules/x.js` es bloqueado | Denylist enforcement |
| `test_max_tool_calls_limit` | Error si > 50 tool calls registrados | Bloat protection |
| `test_bundle_capture_disabled_by_default` | Sin flag `--bundle-capture`, recorder es noop | Backward compat |
| `test_concurrent_recorders_isolated` | Dos run_ids diferentes no se cruzan | Isolation |
| `test_file_read_outside_segment_blocked` | Read de `/etc/passwd` es prohibido | Security scope |
| `test_bundle_finalization_retry` | Retry 3 veces si write fail, luego warning | Resilience |
| `test_bundle_show_command_output` | CLI muestra manifest en formato legible | UX |

#### 3.1.3 Comandos CLI Nuevos

```bash
# Capturar bundle durante un run
trifecta ctx search --segment . --query "test" --bundle-capture

# Inspeccionar bundle generado
trifecta bundle show run_1735772400

# Listar bundles disponibles
trifecta bundle list --segment .
```

#### 3.1.4 Rollback Plan

- Si `BundleRecorder` causa crashes: Deshabilitar con `--bundle-capture=false` (default).
- Si policy YAML es inválido: Fallar ruidosamente (`ctx bundle show` muestra error, no silent fallback).
- Si manifest corrupto: Eliminar `_ctx/bundles/<run_id>/` y re-run sin bundle capture.

---

### 3.2 Iteración 2: Background Task Runner (Week 2)

**Objetivo**: Ejecutar comandos largos (ej: `load` con full scan, `build` con AST parsing) en background con state tracking.

#### 3.2.1 Definition of Done (DoD)

- [ ] Módulo `src/infrastructure/background_task_manager.py` con:
  - `BackgroundTaskManager.start(command, args) -> task_id`
  - `BackgroundTaskManager.status(task_id) -> TaskState`
  - `BackgroundTaskManager.tail(task_id, lines=20) -> str`
  - `BackgroundTaskManager.cancel(task_id) -> bool`
- [ ] State machine para tasks:
  ```
  PENDING → RUNNING → DONE
               ↓
             FAILED ← TIMEOUT
               ↓
           CANCELLED
  ```
- [ ] State file `_ctx/tasks/<task_id>/state.json`:
  ```json
  {
    "task_id": "task_abc123",
    "command": "trifecta ctx build",
    "args": {"segment": "."},
    "state": "RUNNING",
    "started_at": "2026-01-01T12:05:00Z",
    "updated_at": "2026-01-01T12:05:10Z",
    "pid": 12345,
    "log_path": "_ctx/tasks/task_abc123/output.log"
  }
  ```
- [ ] Lockfile `_ctx/tasks/<task_id>/task.lock` (fcntl) para evitar multi-writer.
- [ ] Report streaming: Task escribe a `output.log` (append-only), `tail` command lee últimas N líneas.
- [ ] Timeout policy: Si task > 10 mins sin heartbeat, marcar como TIMEOUT.
- [ ] CLI commands:
  ```bash
  trifecta background start "ctx build --segment ."  # Returns task_id
  trifecta background ps                              # List all tasks
  trifecta background tail <task_id>                  # Stream last 20 lines
  trifecta background cancel <task_id>                # Send SIGTERM
  ```
- [ ] Test: `tests/unit/test_background_task_manager.py` con 12 tests (state transitions, timeout, cancel, concurrent tasks).
- [ ] Integration test: `tests/test_background_integration.py` con real subprocess spawn.

#### 3.2.2 Tests Required

| Test | Assertion | Coverage |
|------|-----------|----------|
| `test_start_task_creates_state_file` | `state.json` existe con state=PENDING | Happy path |
| `test_task_transitions_to_running` | Después de spawn, state=RUNNING | State machine |
| `test_task_transitions_to_done_on_success` | Exit 0 → state=DONE | Success path |
| `test_task_transitions_to_failed_on_error` | Exit 1 → state=FAILED | Error path |
| `test_timeout_marks_task_as_timeout` | Mock 10min delay → state=TIMEOUT | Timeout policy |
| `test_cancel_sends_sigterm` | cancel() envía SIGTERM a PID | Cancellation |
| `test_concurrent_tasks_isolated` | Task A y Task B no comparten state | Isolation |
| `test_lockfile_prevents_multi_writer` | Segundo start con mismo task_id falla con error | Concurrency safety |
| `test_tail_reads_last_20_lines` | tail() retorna últimas 20 líneas de output.log | Streaming |
| `test_ps_lists_all_tasks` | ps() retorna lista de task_ids con states | Discovery |
| `test_stale_lock_cleanup` | Lock > 1hr sin heartbeat es removido | Stale lock detection |
| `test_task_output_log_rotation` | Log > 5MB → rotate (keep last 2 files) | Bloat protection |

#### 3.2.3 Comandos CLI Nuevos

```bash
# Iniciar background task
trifecta background start "ctx build --segment ."
# Output: Task started: task_abc123

# Listar tasks activos
trifecta background ps
# Output:
# task_abc123  RUNNING  ctx build  2min ago
# task_def456  DONE     ctx sync   5min ago

# Ver output de task
trifecta background tail task_abc123
# Output: [streaming last 20 lines]

# Cancelar task
trifecta background cancel task_abc123
# Output: Task cancelled (SIGTERM sent)
```

#### 3.2.4 Rollback Plan

- Si background tasks causan zombies: Implementar `cleanup` command que mata PIDs stale.
- Si lockfile corrupto: Eliminar `_ctx/tasks/<task_id>/*.lock` manualmente y re-start.
- Si state.json inválido: Comando `ps` marca como UNKNOWN y sugiere cleanup.

---

### 3.3 Iteración 3: AST/LSP Events en Bundles (Week 4)

**Objetivo**: Capturar eventos LSP (code definitions, references) y AST parsing como parte del bundle para reproducibilidad avanzada.

#### 3.3.1 Definition of Done (DoD)

- [ ] Feature flag `TRIFECTA_BUNDLE_CAPTURE_AST=1` en `.env` (off by default).
- [ ] Módulo `src/infrastructure/lsp_event_recorder.py` con:
  - `LSPEventRecorder.log_request(method, params)`
  - `LSPEventRecorder.log_response(method, result)`
  - `LSPEventRecorder.log_timeout(method, duration_ms)`
- [ ] Integración con pyright/pylance LSP (opcional, graceful degradation si no disponible):
  - Si LSP server no responde en 2s → log timeout event, continuar sin AST.
  - Si LSP devuelve error → log error event, no crashear.
- [ ] Bundle event schema extendido:
  ```json
  {
    "tool_calls": [
      {
        "id": "tc_005",
        "name": "lsp.textDocument/definition",
        "args": {"uri": "file:///.../use_cases.py", "position": {"line": 42, "char": 10}},
        "result": {"definitions": [{"uri": "...", "range": {...}}]},
        "timing_ms": 150,
        "lsp_server": "pyright@1.1.350"
      }
    ]
  }
  ```
- [ ] Policy: AST events son opt-in (requiere flag explícito).
- [ ] Test: `tests/unit/test_lsp_event_recorder.py` con 8 tests (timeout, error, graceful degradation).
- [ ] Integration test: `tests/test_lsp_integration.py` con mock LSP server.

#### 3.3.2 Tests Required

| Test | Assertion | Coverage |
|------|-----------|----------|
| `test_lsp_event_capture_disabled_by_default` | Sin feature flag, LSP events no se capturan | Default behavior |
| `test_lsp_request_logged` | textDocument/definition request se graba | Happy path |
| `test_lsp_timeout_logged_no_crash` | Timeout de LSP → log event, continuar | Resilience |
| `test_lsp_error_logged_no_crash` | Error LSP → log event, continuar | Error handling |
| `test_bundle_with_ast_events_replayable` | Bundle replay puede skip LSP events si no disponible | Replay compatibility |
| `test_ast_events_excluded_from_bundle_if_too_large` | Si AST events > 2MB, solo metadata (no full result) | Bloat protection |
| `test_lsp_server_unavailable_fallback` | Si pyright no instalado → log warning, disable AST capture | Graceful degradation |
| `test_bundle_manifest_includes_lsp_version` | Manifest tiene `lsp_server: "pyright@version"` | Versioning |

#### 3.3.3 Comandos CLI Nuevos

```bash
# Habilitar AST capture (una vez)
export TRIFECTA_BUNDLE_CAPTURE_AST=1

# Run con AST events
trifecta ctx build --segment . --bundle-capture

# Inspeccionar bundle con AST events
trifecta bundle show run_xyz --include-ast
# Output: [muestra LSP tool calls]

# Replay sin AST (mock)
trifecta bundle replay run_xyz --skip-ast
```

#### 3.3.4 Rollback Plan

- Si LSP hangs: Timeout hard-coded 2s, luego disable AST capture automáticamente.
- Si AST events explotan bundle size: Aplicar limit (2MB max por bundle), truncar resto.
- Si pyright no disponible: Feature flag auto-disabled, continuar sin AST.

---

## 4. ESPECIFICACIÓN MÍNIMA DE FORMATOS

### 4.1 `manifest.json` (Bundle Manifest v1)

```json
{
  "schema_version": 1,
  "run_id": "run_1735772400",
  "created_at": "2026-01-01T12:00:00Z",
  "segment": "trifecta_dope",
  "command": {
    "name": "ctx search",
    "args": {
      "query": "validate segment",
      "segment": ".",
      "limit": 5
    }
  },
  "environment": {
    "python_version": "3.12.1",
    "uv_version": "0.1.18",
    "os": "Linux",
    "cwd": "/workspaces/trifecta_dope"
  },
  "tool_calls": [
    {
      "id": "tc_001",
      "parent_id": null,
      "name": "ctx.search",
      "args": {"query": "validate segment"},
      "result": {
        "hits": [
          {"id": "agent:39151e4814", "score": 0.50, "preview": "..."}
        ]
      },
      "timing_ms": 45,
      "timestamp": "2026-01-01T12:00:01.123Z",
      "execution_order": 1
    }
  ],
  "file_reads": [
    {
      "path": "_ctx/context_pack.json",
      "sha256": "abc123...",
      "lines_read": [1, 156],
      "char_count": 28989,
      "redacted": false
    }
  ],
  "file_writes": [
    {
      "path": "_ctx/session_trifecta_dope.md",
      "operation": "append",
      "lines_added": 8,
      "sha256_after": "def456..."
    }
  ],
  "policies_applied": {
    "source": "_ctx/ctx_bundle_rules.yaml",
    "sha256": "789abc...",
    "violations": 0
  },
  "metadata": {
    "sha256_digest": "bundle_hash_xyz",
    "bundle_size_bytes": 45678,
    "finalized_at": "2026-01-01T12:00:05.000Z",
    "warnings": []
  }
}
```

**Campos Obligatorios**: `schema_version`, `run_id`, `created_at`, `command`, `tool_calls`, `sha256_digest`.

**Campos Opcionales**: `file_reads`, `file_writes`, `lsp_events` (si AST enabled), `warnings`.

---

### 4.2 `events.jsonl` (Telemetry Extended for Bundles)

Cada línea es un JSON con el formato:

```json
{
  "ts": "2026-01-01T12:00:01.123Z",
  "run_id": "run_1735772400",
  "segment": "trifecta_dope",
  "cmd": "ctx.search",
  "args": {"query": "validate segment", "limit": 5},
  "result": {"status": "ok", "hits": 3},
  "timing_ms": 45,
  "warnings": [],
  "tool_call_id": "tc_001",
  "parent_trace_id": null,
  "execution_order": 1
}
```

**Nuevos Campos para Bundles**:
- `tool_call_id`: UUID único del tool call (para grafos de dependencia).
- `parent_trace_id`: ID del tool call padre (para nested calls).
- `execution_order`: Orden secuencial (para replay determinista).

---

### 4.3 `ctx_bundle_rules.yaml` (Bundle Policy v1)

```yaml
schema_version: 1

# ALLOWLIST: Solo estos paths/patterns son elegibles para bundle
allow:
  - "*.md"
  - "_ctx/context_pack.json"
  - "_ctx/session_*.md"
  - "_ctx/prime_*.md"
  - "_ctx/agent.md"
  - "skill.md"
  - "README.md"

# DENYLIST: Nunca incluir estos paths (trumps allowlist)
deny:
  - "node_modules/**"
  - ".git/**"
  - "**/*.pyc"
  - "**/__pycache__/**"
  - ".env"
  - ".env.*"
  - "**/*secret*"
  - "**/*password*"
  - "**/.venv/**"
  - "**/venv/**"

# LIMITS: Hard caps para prevenir bloat
limits:
  max_bundle_size_mb: 10
  max_file_reads: 100
  max_tool_calls: 50
  max_single_file_mb: 2

# REDACTION: Patterns a redactar en file_reads/tool_call results
redaction:
  enabled: true
  patterns:
    - 'api[_-]?key["\s:=]+[\w-]{20,}'
    - 'password["\s:=]+[^\s"]+'
    - 'token["\s:=]+[\w-]{40,}'
    - 'secret["\s:=]+[\w-]{20,}'
  replacement: "***REDACTED***"

# FAIL POLICY: Qué hacer si se viola una regla
fail_policy:
  on_deny_match: "skip_with_warning"  # skip_with_warning | fail_loudly
  on_size_exceeded: "truncate"         # truncate | fail_loudly
  on_redaction_match: "redact"         # redact | fail_loudly
```

---

### 4.4 `task_state.json` (Background Task State)

```json
{
  "schema_version": 1,
  "task_id": "task_abc123",
  "command": {
    "name": "ctx build",
    "args": {"segment": "."}
  },
  "state": "RUNNING",
  "state_history": [
    {"state": "PENDING", "timestamp": "2026-01-01T12:05:00Z"},
    {"state": "RUNNING", "timestamp": "2026-01-01T12:05:01Z"}
  ],
  "started_at": "2026-01-01T12:05:00Z",
  "updated_at": "2026-01-01T12:05:15Z",
  "heartbeat_last": "2026-01-01T12:05:15Z",
  "process": {
    "pid": 12345,
    "cwd": "/workspaces/trifecta_dope",
    "env": {
      "TRIFECTA_TELEMETRY_LEVEL": "lite"
    }
  },
  "output": {
    "log_path": "_ctx/tasks/task_abc123/output.log",
    "log_size_bytes": 4567,
    "last_lines": ["Building context pack...", "7 chunks created"]
  },
  "result": null,
  "error": null,
  "timeout_at": "2026-01-01T12:15:00Z"
}
```

**State Transitions**:
- `PENDING → RUNNING`: Task spawn success.
- `RUNNING → DONE`: Exit code 0.
- `RUNNING → FAILED`: Exit code != 0.
- `RUNNING → TIMEOUT`: Heartbeat > 10min stale.
- `RUNNING → CANCELLED`: SIGTERM received.

---

## 5. RIESGOS CRÍTICOS (Top 5) + Mitigación

### 5.1 Riesgo R1: Secrets en Bundles

**Descripción**: Bundle puede capturar `.env`, API keys en file_reads, o secrets en tool_call results.

**Impacto**: CRÍTICO (filtración de credenciales).

**Probabilidad**: ALTA (sin redaction, inevitable en 1–2 runs).

**Mitigación**:
1. **Preventivo**: Denylist estricta en `ctx_bundle_rules.yaml` (`.env`, `*secret*`, `*password*`).
2. **Detective**: Pre-scan con regex patterns antes de bundle pack (ver 4.3 redaction).
3. **Correctivo**: Si secrets detectados → fail bundle pack con error ruidoso (no silent).
4. **Validación**: Test `test_bundle_pack_blocks_secrets` con `.env` mock.

**Métrica**: `secrets_detected_count` > 0 → FAIL build.

---

### 5.2 Riesgo R2: node_modules / .git Bloat

**Descripción**: Si `scan_files()` captura `node_modules/` o `.git/`, bundle puede ser GBs.

**Impacto**: ALTO (disk exhaustion, bundle unshippable).

**Probabilidad**: MEDIA (fácil de triggerear con workspace con node_modules).

**Mitigación**:
1. **Preventivo**: Hardcoded denylist en `FileSystemAdapter.scan_files()` (además de policy YAML).
2. **Detective**: Check `bundle_size_mb` antes de finalize, abort si > 10MB.
3. **Correctivo**: Comando `trifecta bundle prune <run_id>` para eliminar bloat post-mortem.
4. **Validación**: Test `test_bundle_scan_excludes_node_modules` con workspace real.

**Métrica**: `excluded_paths_count` debe ser > 0 en workspaces típicos.

---

### 5.3 Riesgo R3: Multi-Writer Corruption (context_pack.json)

**Descripción**: Dos `trifecta ctx build` concurrentes escriben a `context_pack.json` sin lock.

**Impacto**: CRÍTICO (pack corrupto → validation FAIL → pipeline blocked).

**Probabilidad**: BAJA en MVP (uso single-agent), ALTA en multi-agent future.

**Mitigación**:
1. **Preventivo**: Agregar lockfile `_ctx/context_pack.lock` (fcntl.LOCK_EX) en `BuildContextPackUseCase`.
2. **Detective**: Validar SHA256 de pack después de write, retry si mismatch.
3. **Correctivo**: Si lock busy > 30s, fail con error `Another build in progress`.
4. **Validación**: Test `test_concurrent_builds_block` con multiprocessing.

**Métrica**: `build_lock_contention_count` (cuántas veces se esperó lock).

---

### 5.4 Riesgo R4: Stale Locks

**Descripción**: Proceso crashea sin liberar lock, dejando `task.lock` stale forever.

**Impacto**: MEDIO (task bloqueada, requiere manual cleanup).

**Probabilidad**: MEDIA (crashes son raros pero no imposibles).

**Mitigación**:
1. **Preventivo**: Lockfile con timestamp + PID, TTL de 1hr.
2. **Detective**: `trifecta background ps` detecta locks > 1hr y marca como STALE.
3. **Correctivo**: Comando `trifecta background cleanup` elimina locks stale (after confirming PID dead).
4. **Validación**: Test `test_stale_lock_cleanup_after_1hr`.

**Métrica**: `stale_lock_cleanup_count` (cuántos locks fueron limpiados).

---

### 5.5 Riesgo R5: Environment Drift (Bundle Replay Fails)

**Descripción**: Bundle capturado en Python 3.12, replay en 3.11 → imports fail, AST incompatible.

**Impacto**: MEDIO (replay no reproducible, bundle inútil para debug).

**Probabilidad**: ALTA (entornos heterogéneos comunes).

**Mitigación**:
1. **Preventivo**: Bundle manifest incluye `python_version`, `uv_version`, `os` (ver 4.1).
2. **Detective**: `trifecta bundle replay` verifica versiones, warn if mismatch.
3. **Correctivo**: Replay mode con `--ignore-env-mismatch` para best-effort (con disclaimer).
4. **Validación**: Test `test_bundle_replay_warns_on_env_mismatch`.

**Métrica**: `replay_env_mismatch_count` (cuántos replays tuvieron drift).

---

## 6. CHECKLIST DE VALIDACIÓN (PASS/FAIL)

Usa este checklist para auditar la implementación post-MVP:

| # | Criterio | PASS | FAIL | Evidencia |
|---|----------|------|------|-----------|
| **V1** | Bundle manifest incluye `tool_calls` con `execution_order` | ☐ | ☐ | `manifest.json` tiene campo `execution_order` en cada tool_call |
| **V2** | Bundle policy YAML tiene denylist con `node_modules`, `.git`, `.env` | ☐ | ☐ | `ctx_bundle_rules.yaml` contiene al menos 3 deny patterns |
| **V3** | Redaction aplicada a secrets (API keys, passwords) | ☐ | ☐ | Test `test_log_tool_call_with_redaction` PASS |
| **V4** | Background tasks usan lockfile (no multi-writer) | ☐ | ☐ | `task.lock` existe durante `RUNNING` state |
| **V5** | Stale locks son detectados y limpiables | ☐ | ☐ | `trifecta background cleanup` elimina locks > 1hr |
| **V6** | Bundle pack pre-scans para secrets antes de tar.gz | ☐ | ☐ | `trifecta bundle pack` falla si secrets detectados |
| **V7** | Context pack build usa lockfile para evitar split-brain | ☐ | ☐ | `context_pack.lock` creado en `BuildContextPackUseCase` |
| **V8** | Telemetry events tienen `tool_call_id` para tracing | ☐ | ☐ | `events.jsonl` líneas incluyen `tool_call_id` |
| **V9** | AST events son opt-in (feature flag) | ☐ | ☐ | Sin `TRIFECTA_BUNDLE_CAPTURE_AST=1`, no LSP events |
| **V10** | Bundle size límite (10MB) enforced | ☐ | ☐ | `trifecta bundle pack` falla si > 10MB |
| **V11** | Background task timeout (10min) funcional | ☐ | ☐ | Task sin heartbeat > 10min → state=TIMEOUT |
| **V12** | Bundle replay no ejecuta side-effects (dry-run only) | ☐ | ☐ | FileSystemAdapter.write() es mock en replay mode |
| **V13** | Session append usa AtomicWriter (no half-writes) | ☐ | ☐ | `SessionAppendUseCase` usa `AtomicWriter.write()` |
| **V14** | Fail-closed: Bundle pack abort si policy violation | ☐ | ☐ | `fail_policy: fail_loudly` fuerza abort |
| **V15** | Bundle manifest SHA256 es verificable | ☐ | ☐ | `sha256 manifest.json` matches `metadata.sha256_digest` |

**Criterio de Aprobación**: Mínimo **13/15 PASS** para MVP acceptance.

---

## APÉNDICE A: Instrumentación Hooks (Dónde Agregar Código)

### A.1 CLI → Bundle Recorder Hook

**Archivo**: `src/infrastructure/cli.py`

**Punto de inserción**: Inicio de cada comando (después de `_get_telemetry`, antes de UseCase.execute).

```python
# cli.py (ejemplo en ctx_app.command("search"))

@ctx_app.command("search")
def search(...):
    telemetry = _get_telemetry(segment, telemetry_level)
    
    # NUEVO: Bundle recorder hook
    bundle_recorder = None
    if typer.get_context().params.get("bundle_capture", False):
        bundle_recorder = BundleRecorder(segment, run_id=telemetry.run_id)
        bundle_recorder.start_session("ctx search", {"query": query, "limit": limit})
    
    use_case = SearchUseCase(file_system, telemetry, bundle_recorder)  # Inject recorder
    # ...
```

**Impacto**: Cada comando necesita pasar `bundle_recorder` a UseCase (signature change).

---

### A.2 UseCase → Tool Call Logging

**Archivo**: `src/application/search_get_usecases.py`

**Punto de inserción**: Dentro de `SearchUseCase.execute`, después de `service.search()`.

```python
# search_get_usecases.py

def execute(self, target_path, query, limit):
    result = service.search(term, k=limit * 2)
    
    # NUEVO: Log tool call to bundle
    if self.bundle_recorder:
        self.bundle_recorder.log_tool_call(
            name="ctx.search",
            args={"query": query, "limit": limit},
            result={"hits": len(result.hits)},
            timing_ms=elapsed_ms
        )
    
    # ... rest of formatting
```

---

### A.3 FileSystemAdapter → File Read Tracking

**Archivo**: `src/infrastructure/file_system.py`

**Punto de inserción**: En `scan_files()` y `read_text()` wrappers.

```python
# file_system.py

class FileSystemAdapter:
    def __init__(self, bundle_recorder=None):
        self.bundle_recorder = bundle_recorder
    
    def read_text(self, path: Path) -> str:
        content = path.read_text()
        
        # NUEVO: Log file read to bundle
        if self.bundle_recorder:
            self.bundle_recorder.log_file_read(
                path=str(path),
                lines_read=[1, len(content.splitlines())],
                char_count=len(content)
            )
        
        return content
```

---

### A.4 Background Task → State Machine Updates

**Archivo**: `src/infrastructure/background_task_manager.py` (nuevo)

**Estado tracking**: Cada transición escribe a `_ctx/tasks/<task_id>/state.json` con lock.

```python
# background_task_manager.py (nuevo archivo)

class BackgroundTaskManager:
    def _update_state(self, task_id: str, new_state: str):
        state_path = self._task_dir(task_id) / "state.json"
        lock_path = self._task_dir(task_id) / "task.lock"
        
        with file_lock(lock_path):
            state = json.loads(state_path.read_text())
            state["state"] = new_state
            state["updated_at"] = datetime.now().isoformat()
            state["state_history"].append({"state": new_state, "timestamp": state["updated_at"]})
            
            AtomicWriter.write(state_path, json.dumps(state, indent=2))
```

---

## APÉNDICE B: Dependencias Externas

| Dependencia | Versión | Propósito | Risk | Fallback |
|-------------|---------|-----------|------|----------|
| `fcntl` (stdlib) | Python 3.12+ | File locking (POSIX) | LOW (Windows no soporta) | Skip locking en Windows con warning |
| `hashlib` (stdlib) | Python 3.12+ | SHA256 para manifest integrity | NONE | N/A |
| `subprocess` (stdlib) | Python 3.12+ | Background task spawn | LOW (shell injection risk) | Sanitize args con shlex.quote |
| `pyright` (LSP, opcional) | 1.1.350+ | AST events para bundles | HIGH (external binary) | Graceful degradation si no disponible |
| `pyyaml` (existente) | 6.0+ | Policy YAML parsing | NONE (ya usado) | N/A |

**Nota**: NO agregar dependencias nuevas pesadas (ej: tree-sitter, numpy) para MVP. Usar stdlib siempre que sea posible.

---

## CONCLUSIONES

Este análisis identificó **12 puntos de integración** viables para Background Tasks y Context Bundles en Trifecta, con **3 iteraciones MVP** de implementación incremental (bundle recorder → background runner → LSP events). Los **5 riesgos críticos** (secrets, bloat, multi-writer, stale locks, env drift) tienen mitigaciones concretas y metricas de validación.

**Recomendación ejecutiva**: Implementar **Iteración 1 (Bundle Recorder)** primero (week 1, bajo riesgo, alto valor para debug), validar con checklist V1-V8, luego evaluar ROI antes de proceder con Iteración 2-3.

**Próximos pasos**:
1. Socializar este análisis con stakeholders (team review).
2. Crear issues en GitHub para cada iteración con DoD expandido.
3. Asignar ownership: Bundle Recorder (Junior Dev), Background Runner (Senior Dev), LSP Events (Architect + fallback planning).

---

**Auditoría completada el**: 2026-01-01  
**Auditor**: GitHub Copilot (Claude Sonnet 4.5)  
**Versión del documento**: 1.0
