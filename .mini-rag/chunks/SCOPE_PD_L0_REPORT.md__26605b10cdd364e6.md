### 3. Límites y Truncado
- **Presupuesto**: Default 1200–1500 tokens (`budget_token_est`).
- **Truncado de Chunks**: Si un chunk individual excede el presupuesto en modo `raw`, se reduce a 20 líneas con una nota (Backpressure).
- **Truncado de Lista**: `ctx get` deja de procesar IDs si ya alcanzó el presupuesto.
