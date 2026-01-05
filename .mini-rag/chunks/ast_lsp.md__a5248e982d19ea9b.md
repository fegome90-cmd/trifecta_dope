### T3. CLI commands: `ast symbols`, `ast locate`, `ast snippet`

**Descripción:** herramientas mínimas para que el agente navegue sin abrir todo.
**DoD**

* `ast symbols --query AuthManager` lista candidatos.
* `ast locate sym://py/...` devuelve rango actual.
* `ast snippet sym://... --lines 30` devuelve contexto acotado.
  **Tests**
* CLI e2e con fixtures.
* Si símbolo no existe → salida fail-closed (no inventa).
  **Métrica**
* `snippet_bytes_served` (debe bajar vs “read file”)

---
