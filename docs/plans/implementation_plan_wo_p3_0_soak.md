# Implementation Plan: WO-P3.0 AST Cache Soak Run (Micro-Tasks)

## Goal
Obtain **real field evidence** (not contractual) of AST Cache operability under load.
Validate: hit/miss progression available, lock_wait presence, and DB integrity.

## Strict Constraints
- **NO Pytest** for soak harness.
- **NO Performance Gates** (e.g. p95 < 10ms is flaky).
- **Separate Commits** per micro-task.
- **Parametric Harness** (OPS, WORKERS).

## Micro-Tasks Strategy

### TASK 1: Read & Anchor (Zero-Code)
- **Goal**: Quote exact lines for telemetry emission, DB path compilation, and persistence activation.
- **Gate**: 6-10 lines of verified code evidence.
- **Commit**: None (just validation).

### TASK 2: Harness Mínimo (`eval/scripts/run_ast_cache_soak.sh`)
- **Goal**: Parametric bash script (OPS, WORKERS).
- **Logic**: 
  - Clean `_ctx/telemetry/events.jsonl` (or isolate run).
  - Clean DB (deterministic path).
  - Run `trifecta ast symbols` in parallel.
- **Gate**: Script exits 0 with OPS=10.
- **Commit**: `feat(eval): add ast cache soak harness (parametric)`

### TASK 3: Metrics Extractor (`eval/scripts/extract_ast_soak_metrics.py`)
- **Goal**: Parse JSONL telemetry and output `_ctx/metrics/ast_soak_run.json`.
- **Metrics**: 
  - Counts: hit/miss/write, lock_wait, lock_timeout.
  - Latency: p50, p95 (informational only).
- **Gate**: Valid JSON output from real log.
- **Commit**: `feat(eval): add ast soak metrics extractor`

### TASK 4: Deterministic Gate (`eval/scripts/gate_ast_soak.py`)
- **Goal**: Verify Pass/Fail based on STABLE criteria.
- **Criteria**:
  - `integrity_check == "ok"`
  - `ops_total >= OPS`
  - `cache_hits_warm > 0`
  - `lock_timeout <= 1` (tolerance for rare race)
- **Gate**: Validates success/failure correctly.
- **Commit**: `test(eval): add deterministic soak gates`

### TASK 5: Real Run (200 ops) + Evidence
- **Exec**: `TRIFECTA_AST_PERSIST=1 OPS=200 WORKERS=4 bash eval/scripts/run_ast_cache_soak.sh`
- **Output**:
  - `_ctx/logs/wo_p3_0/soak_run.log`
  - `_ctx/metrics/ast_soak_run.json`
- **Commit**: `feat(eval): record ast soak run P3.0 evidence`

### TASK 6: Governance
- **Actions**:
  - Update `_ctx/session_trifecta_dope.md`
  - Close `WO-P3.0.yaml` (status: done, verified_at_sha: <SHA>, evidence_logs: [...])
  - Update `backlog.yaml` (if applicable)
- **Commit**: `docs(ast): close WO-P3.0 soak audit-grade`
