### Instrumentation Targets (PR#2 will measure)

- AST skeleton build latencies (Tree-sitter parse times + caching)
- LSP lifecycle with state machine (COLD → WARMING → READY → FAILED)
- LSP warm-up policy (parallel spawn during AST build, READY-only gating)
- LSP request latencies (definition, hover, diagnostics) when READY
- Bytes read per command and per disclosure mode
- Fallback triggers (LSP not READY → use AST-only)
