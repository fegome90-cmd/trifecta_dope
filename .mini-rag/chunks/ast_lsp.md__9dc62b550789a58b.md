### T6. Set mínimo de requests LSP

**Implementar solo:**

* `textDocument/definition`
* `textDocument/references`
* `textDocument/hover`
* `textDocument/publishDiagnostics` (capturar notificaciones) ([Microsoft en GitHub][4])
  **DoD**
* `lsp definition selector` retorna location(s)
* `lsp hover selector` retorna firma/docstring
* `diagnostics` se captura y se puede consultar
  **Tests**
* Hover devuelve algo no vacío en símbolo conocido.
* Diagnostics: introducir error en fixture y comprobar que lo reporta.
  **Métrica**
* `lsp_request_success_rate`
* `diagnostics_latency_ms`

---
