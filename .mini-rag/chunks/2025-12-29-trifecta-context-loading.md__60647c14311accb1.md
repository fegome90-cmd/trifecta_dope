## Arquitectura Core: Context as API (Plan A)

La arquitectura principal es **Programmatic Context Calling**. El contexto se trata como herramientas (tools) invocables para descubrir y traer evidencia bajo demanda.

- **Plan A (DEFAULT)**:
  - `ctx.search`: Descubrimiento vía L0 (Digest + Index).
  - `ctx.get`: Consumo con **Progressive Disclosure** (mode=excerpt|raw|skeleton) + **Budget/Backpressure**.
  - **Política**: Máximo 1 search + 1 get por turno. Batching de IDs obligatorio.
  - **Cita**: Siempre citar `[chunk_id]` en la respuesta.

- **Plan B (FALLBACK)**:
  - `ctx load --mode fullfiles`: Carga archivos completos usando selección heurística.
  - Se activa si no existe el pack o si el usuario fuerza el modo.
