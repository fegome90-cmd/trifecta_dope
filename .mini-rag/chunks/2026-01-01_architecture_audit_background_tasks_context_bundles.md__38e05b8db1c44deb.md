| Artefacto | Writer(s) | Lock Strategy | Risk | **v1.1 Update** |
|-----------|-----------|---------------|------|-----------------|
|-----------|-----------|---------------|------|
| Artefacto | Writer(s) | Lock Strategy | Risk | **v1.1 Update** |
|-----------|-----------|---------------|------|-----------------|
| `_ctx/context_pack.json` | BuildContextPackUseCase (solo) | **NONE** ⚠️ | Split-brain si 2 builds concurrentes | **Schema v1 con digest/index/chunks** |
| `_ctx/session_*.md` | SessionAppendUseCase (append) | AtomicWriter (temp+rename) | Race condition en append sin coordinator | Mismo riesgo |
| `_ctx/telemetry/events.jsonl` | Telemetry.event (multi-caller) | fcntl.LOCK_EX + LOCK_NB (skip if busy) | Log loss acceptable (design choice) | Mismo comportamiento |
| `_ctx/telemetry/metrics.json` | Telemetry.flush (once per run) | Single-writer (no concurrent runs expected) | Safe for MVP | **PCC metrics agregados** |
| `_ctx/telemetry/last_run.json` | Telemetry.flush | Overwrite-safe (single writer) | Safe | Mismo |
| `skill.md`, `prime_*.md`, `agent.md` | Human/Agent edits (infrequent) | **NONE** | Assumed low contention | **FP Gate valida estructura** |
| `_ctx/aliases.yaml` | AliasLoader (read-only in code) | N/A | Safe (read-only) | Mismo |
| `_ctx/prime_*.md` → feature_map (NEW) | Human edits (PRIME index) | **NONE** | Safe (read-only by PCC metrics) | **Usado por
