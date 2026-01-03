# SCOPE_READING_BEHAVIOR_REPORT.md

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

## B) Evidencia empírica

### 1. `uv run trifecta ctx search -s . -q "Trifecta"`
```
Search Results (1 hits):
1. [ref:trifecta_dope/README.md:c2d9ad0077] README.md
   Score: 1.00 | Tokens: ~3347
   Preview: # Trifecta Generator...
```

### 2. `uv run trifecta ctx get -s . -i "ref:...README.md..." --mode excerpt`
- **Tokens**: ~264
- **Salida**: Primeras 25 líneas + nota de truncado funcional.

### 3. `uv run trifecta ctx get -s . -i "ref:...README.md..." --mode skeleton`
- **Tokens**: ~416 (debido a la gran cantidad de headers en README.md).
- **Salida**: Solo estructura de headers y bloques de código.

### 4. Backpressure Evidence (`mode=raw`, budget=500)
Al intentar cargar 4 chunks con budget 500:
- El primer chunk se trunca a 20 líneas (Nota: "> [!NOTE] Chunk truncado por presupuesto...").
- El segundo chunk se procesa parcialmente.
- **Señal**: Los últimos chunks de la lista NO se retornan (Loop break).
- **Telemetría**: Evento `ctx.get` marca `trimmed: true` y `total_tokens: 457`.

---

## C) ¿Hay early-stop real?

- **En el código**: **NO EXISTE** una condición de stop basada en "evidencia encontrada". El stop es puramente por *presupuesto de tokens* (Backpressure).
- **En la CLI**: Existe el límite `budget_token_est`. No hay límites de `max_chunks` o `max_chars` explícitos fuera de la estimación de tokens.
- **En telemetría**: **NO EXISTE** el campo `stop_reason`. Solo se infiere el stop si `trimmed: true` en el evento `ctx.get`.

---

## D) Gap list

| Gap | Qué falta | Dónde tocar | Riesgo | Tamaño |
|-----|-----------|-------------|--------|--------|
| **1. Stop Reason Telemetry** | Campo `stop_reason` (`budget`, `complete`, `error`) en el evento `ctx.get`. | `ContextService.get` y `GetChunkUseCase` | Imposible distinguir si el agente paró porque terminó o porque se quedó sin tokens. | S |
| **2. Consumo real de caracteres** | Tracking de `chars_read` y `chunks_total` en telemetría. | `GetChunkUseCase.execute` | El sistema solo estima tokens (chars/4), perdiendo precisión sobre la carga real del prompt. | S |
| **3. Early-Stop por prioridad** | Regla para dejar de cargar chunks de baja prioridad si los de alta prioridad ya alcanzan un umbral de confianza (threshold). | `ContextService.get` | El agente consume tokens en chunks irrelevantes solo porque están en la lista de IDs solicitada. | M |
| **4. Mode "Auto" PD** | Lógica para degradar de `raw` a `excerpt` automáticamente según el ranking de búsqueda. | `ContextService.get` | Mayor latencia y costo al cargar archivos completos que no son el "Top 1" hit. | M |
| **5. Measurement of Stubs/Skeletons** | Separar telemetría de tokens "útiles" vs tokens "estructurales" (overhead). | `ContextService` | No sabemos qué porcentaje del presupuesto se desperdicia en leer skeletons. | S |
