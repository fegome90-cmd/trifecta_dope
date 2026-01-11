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
