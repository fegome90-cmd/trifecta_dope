### T8. `probe_events.jsonl` append-only para AST/LSP

**DoD**

* Registra: `ast_query`, `lsp_request`, `lsp_response_meta`, `repo_sha`, `dirty`, `file_sha`, `duration_ms`, `execution_order`.
* No guarda contenido completo; guarda hashes + paths + ranges.
  **Tests**
* Append-only, orden monotónico.
* No filtra secretos (no logging de contenido).
  **Métrica**
* `probe_event_coverage` (≥90% de queries instrumentadas)

---
