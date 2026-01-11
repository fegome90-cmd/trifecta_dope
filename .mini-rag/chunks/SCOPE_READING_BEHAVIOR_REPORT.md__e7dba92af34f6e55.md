## A) Mapa de lectura (CLI → Use Case → Storage)

1. **`trifecta ctx search`**:
   - **CLI**: Captura query y limit.
   - **`SearchUseCase`**: Normaliza, expande alias y delega a `ContextService`. Combina resultados de múltiples términos expandidos.
   - **`ContextService.search`**: Realiza keyword matching heurístico sobre el `index` de `context_pack.json`.
   - **Retorno**: `SearchHit` con `id`, `preview`, `score` y `token_est`.

2. **`trifecta ctx get`**:
   - **CLI**: Recibe IDs, `mode` (`raw`, `excerpt`, `skeleton`) y `budget_token_est`.
   - **`GetChunkUseCase`**: Envuelve la llamada al servicio y registra telemetría.
   - **`ContextService.get`**:
     - Itera sobre los IDs.
     - Aplica transformación según `mode`.
     - **Budget Control**: Si el modo es `raw` y el chunk excede el budget, lo trunca a 20 líneas (Backpressure).
     - **Loop Stop**: Si el acumulado de tokens supera el budget, rompe el ciclo y deja de procesar IDs.
   - **Retorno**: `GetResult` con lista de chunks (posiblemente truncados) y `total_tokens`.

3. **Definiciones clave**:
   - **Chunk Size**: Definido durante el build (v1: `whole_file`).
   - **Presupuesto**: Usuario define `--budget-token-est` (default 1500).
   - **Modos**: `raw`, `excerpt`, `skeleton`. No existe un modo `auto` real basado en relevancia.

---
