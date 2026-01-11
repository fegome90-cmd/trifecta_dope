**Recomendaciones priorizadas**:
1. **MVP-1 (Bundle Recorder)**: Agregar `ContextBundleRecorder` a CLI como wrapper de telemetry, capturando stdin/stdout + tool_calls + file_reads (week 1, low-risk).
2. **MVP-2 (Background Runner)**: Implementar `BackgroundTaskManager` con state machine (running/done/failed) y lockfile en `_ctx/tasks/` (week 2, med-risk por concurrency).
3. **MVP-3 (LSP Events)**: Instrumentar AST/LSP events como opcionales en bundles, con feature-flag y fallback-ready (week 4, high-risk por external dependency).

---
