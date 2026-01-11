## E) Conclusión de scope

- **PD existe**: **PARCIAL**. Está implementado el mecanismo de *modos* (excerpt/skeleton) y *presupuesto*, pero falta el trigger automático basado en *Score* que menciona el README.
- **L0 Skeleton cumple**: **SÍ**. El skeletonizador es determinista y extrae firmas y estructura correctamente.
- **Gaps concretos**:

| Gap | Dónde tocar | Riesgo si no se corrige | Tamaño |
|-----|-------------|-------------------------|--------|
| **1. Score-based Auto PD** | `ContextService.get` | El agente debe elegir manualmente el modo; mayor carga cognitiva. | M |
| **2. Skeleton Signatures (JS/TS)** | `ContextService._skeletonize`| Soporte pobre para otros lenguajes fuera de Python (keywords hardcoded). | S |
| **3. Search keyword recall** | `ContextService.search` | Chunks relevantes no se encuentran si el término no está en el preview truncado. | M |
| **4. Budget Backpressure Hardening**| `ContextService.get` | Sigue acumulando tokens hasta pasarse; el fallback a excerpt es solo para el *último* chunk que no cabe. | S |
| **5. Cross-file Skeleton Index** | `context_pack.json` index | El index no guarda el skeleton pre-calculado; obliga a cargar el `text` completo para skeletonizar. | L |
