## OVERVIEW

This PR will instrument the **existing Trifecta telemetry system** (not create a new one) to measure:
- AST skeleton build latencies (Tree-sitter parse times)
- LSP lifecycle (spawn → initialize → ready)
- LSP request latencies (definition, diagnostics)
- Bytes read per command and per disclosure mode
- Fallback triggers (timeouts, errors)

**Breaking changes:** None. All new fields are additive; existing event format unchanged.

---
