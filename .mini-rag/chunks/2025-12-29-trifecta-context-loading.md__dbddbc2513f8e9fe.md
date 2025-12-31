### Router: Heurística + Hybrid Search

**Plan A (CORE)**: Usa un router heurístico (keyword boosts) para decidir qué chunks buscar. Si el recall falla, se evoluciona a búsqueda híbrida (FTS5 + BM25). **NO se usa un LLM para selección** para evitar latencia y fragilidad.

**Plan B (FALLBACK)**: Carga archivos completos basados en la misma heurística si falta el pack.

---
