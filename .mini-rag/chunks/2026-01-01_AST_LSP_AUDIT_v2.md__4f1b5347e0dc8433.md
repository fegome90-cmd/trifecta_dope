**Metrics:**
- `lsp_definition_count`: Requests sent
- `lsp_cold_start_ms`: P50/P95 time to first response
- `lsp_timeout_count`: Times timeout exceeded (then fallback)
- `lsp_fallback_count`: Times fell back to Tree-sitter

**Rollback Plan:**
- If Pyright cold start >2s: Use subprocess pre-spawn (start in background) + instant fallback
- If IPC overhead >50ms per request: Cache LSP responses in skeleton map
- If diagnostics too noisy: Implement redaction filter (see G: Security)

---
