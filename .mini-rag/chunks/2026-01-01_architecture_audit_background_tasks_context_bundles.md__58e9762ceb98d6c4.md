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
