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
| **V11** | Background task timeout (10min) funcional | ☐ | ☐ | Task sin heartbe
