## Exploration: Trifecta MCP F1 Transformation (Portable Edition)

### Current State
El servidor MCP actual (`tmp_mcp_f1/server.py`) es un satélite que orbita alrededor de una instalación local de Trifecta. Depende de `TRIFECTA_DOPE_DIR` y de que el runner pueda ejecutar subprocesos de `uv`. Esto lo hace imposible de portar a la web o a entornos sin shell.

### Affected Areas
- `tmp_mcp_f1/server.py` — Se reescribirá para ser el "Main Entrypoint" de Trifecta.
- `pyproject.toml` — Se agregarán scripts de consola para que `trifecta-mcp` sea un binario global.
- `src/application/` — Se verificarán las dependencias para asegurar que los UseCases sean importables.

### Approaches
1. **Approach: Embedded Engine (Recomendado)** — El servidor importa `BuildContextPackUseCase`, `SearchUseCase` y `PlanUseCase`.
   - Pros: Portabilidad absoluta, latencia cero, inteligencia total (AST/Graph).
   - Cons: Requiere refactorización de los imports del core.
   - Effort: Medium

2. **Approach: Standalone Binary (PyInstaller)** — Empaquetar todo en un ejecutable.
   - Pros: Un solo archivo.
   - Cons: No sirve para la web (WASM), binario pesado.
   - Effort: High

### Recommendation
**Approach 1: Embedded Engine**. Vamos a convertir a Trifecta en una librería Python moderna que exponga una interfaz MCP de primer nivel.

### Risks
- **WASM Compatibility**: Algunas funciones de AST podrían fallar si dependen de C. (Verificado: Trifecta usa `ast` stdlib, OK).

### Ready for Proposal
Yes.
