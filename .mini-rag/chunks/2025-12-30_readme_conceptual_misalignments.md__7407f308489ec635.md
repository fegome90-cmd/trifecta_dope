### 3. **Mini-RAG sin contexto (L247-265)**

**Ubicación**: `README.md:247-265`

**Problema**:
```markdown
## Mini-RAG (Contexto Local)

Este repo integra Mini-RAG para consultas rápidas sobre la documentación (RAG local).
```

**Por qué es confuso**:

- No aclara que Mini-RAG es **herramienta de desarrollo**, NO parte de Trifecta
- Contradice "Trifecta NO ES un RAG genérico" (L25)
- Los agentes pueden confundir Mini-RAG con el paradigma PCC

**Corrección propuesta**:

```markdown
## 🔧 Mini-RAG (Herramienta de Desarrollo)

> **NOTA**: Mini-RAG es una herramienta **externa** para que TÚ (desarrollador) consultes  
> la documentación del CLI. **NO es parte del paradigma Trifecta.**

Trifecta usa búsqueda lexical (grep-like), NO embeddings.

### Setup (solo para desarrollo del CLI)

```bash
make minirag-setup MINIRAG_SOURCE=~/Developer/Minirag
make minirag-query MINIRAG_QUERY="PCC"
```

**Para agentes**: Usar `trifecta ctx search`, NO Mini-RAG.

```

---
