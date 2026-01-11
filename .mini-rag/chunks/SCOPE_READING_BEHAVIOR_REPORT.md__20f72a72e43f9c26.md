## D) Gap list

| Gap | Qué falta | Dónde tocar | Riesgo | Tamaño |
|-----|-----------|-------------|--------|--------|
| **1. Stop Reason Telemetry** | Campo `stop_reason` (`budget`, `complete`, `error`) en el evento `ctx.get`. | `ContextService.get` y `GetChunkUseCase` | Imposible distinguir si el agente paró porque terminó o porque se quedó sin tokens. | S |
| **2. Consumo real de caracteres** | Tracking de `chars_read` y `chunks_total` en telemetría. | `GetChunkUseCase.execute` | El sistema solo estima tokens (chars/4), perdiendo precisión sobre la carga real del prompt. | S |
| **3. Early-Stop por prioridad** | Regla para dejar de cargar chunks de baja prioridad si los de alta prioridad ya alcanzan un umbral de confianza (threshold). | `ContextService.get` | El agente consume tokens en chunks irrelevantes solo porque están en la lista de IDs solicitada. | M |
| **4. Mode "Auto" PD** | Lógica para degradar de `raw` a `excerpt` automáticamente según el ranking de búsqueda. | `ContextService.get` | Mayor latencia y costo al cargar archivos completos que no son el "Top 1" hit. | M |
| **5. Measurement of Stubs/Skeletons** | Separar telemetría de tokens "útiles" vs tokens "estructurales" (overhead). | `ContextService` | No sabemos qué porcentaje del presupuesto se desperdicia en leer skeletons. | S |
