## 1) North Star (verificable + anti-goals hardened)

**North Star (literal)**:
> "Un agente entienda cualquier segmento del repo en <60 segundos leyendo solo 3 archivos + 1 log."

**Documentado en**: `README.md:L3`

**Anti-goals (NO implican eliminación)**:

1. **Anti-goal**: "Trifecta NO ES un RAG genérico"
   Justificación: No indexamos todo el código para maximizar recall. Trade-off: Optamos por curación manual (prime.md) vs búsqueda exhaustiva.
   Features que PERMANECEN: `ctx search` sigue funcional (búsqueda léxica en context pack), nivel: básico
   Test que valida:
   ```bash
   uv run trifecta ctx search -s . -q "test" --limit 5 | jq 'length' | grep -E '^[0-9]+$'
   ```

2. **Anti-goal**: "Trifecta NO ES una base vectorial / embeddings-first"
   Justificación: No depende de embeddings para no añadir costo/latencia de modelo. Trade-off: Búsqueda léxica es suficiente para docs curados.
   Features que PERMANECEN: Búsqueda keyword-based funcional
   Test que valida:
   ```bash
   # Verifica que NO hay dependencia de sentence-transformers o similar
   rg "sentence-transformers|openai\.Embedding" src/ && exit 1 || exit 0
   ```
