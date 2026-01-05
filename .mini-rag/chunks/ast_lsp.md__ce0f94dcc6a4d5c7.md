### T5. LSP Client headless mínimo (stdio JSON-RPC)

**Lenguaje recomendado para Sprint:** Python con Pyright (`pyright-langserver`).
La LSP spec define JSON-RPC y los eventos clave. ([Microsoft en GitHub][1])
**DoD**

* Arranca servidor, handshake initialize/initialized.
* Timeout duro (ej. 5s). Si excede → fallback AST.
* Cierre limpio del proceso.
  **Tests**
* Unit: mock JSON-RPC framing.
* Integration: arranca pyright y responde `hover` en fixture repo.
  **Métrica**
* `lsp_cold_start_ms` (P50/P95)
* `lsp_timeout_rate` (debe ser bajo, o fallback siempre)
