### 4. Backpressure Evidence (`mode=raw`, budget=500)
Al intentar cargar 4 chunks con budget 500:
- El primer chunk se trunca a 20 líneas (Nota: "> [!NOTE] Chunk truncado por presupuesto...").
- El segundo chunk se procesa parcialmente.
- **Señal**: Los últimos chunks de la lista NO se retornan (Loop break).
- **Telemetría**: Evento `ctx.get` marca `trimmed: true` y `total_tokens: 457`.

---
