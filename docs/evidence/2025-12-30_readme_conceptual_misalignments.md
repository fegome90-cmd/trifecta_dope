# Desalineaciones Conceptuales — README Analysis (REVISADO)

**Fecha**: 2025-12-30  
**Contexto**: Artículo "Advanced Context Use: Context as Invokable Tools" (autor: Felipe González, 2025)  
**Inspiración**: Anthropic's "Advanced Tool Use" pattern  
**Método**: Trifecta CLI + Feedback del usuario

---

## 🎯 Concepto Central (del artículo)

**Trifecta NO es RAG. Es "Programming Context Calling".**

> "Instead of tools, we treat context chunks as invokable resources."  
> — "Advanced Context Use" (aplicando el patrón de Anthropic al contexto)

La analogía 1:1:

- **Tool Search Tool** → **Context Search** (`ctx.search`)
- **Programmatic Tool Calling** → **Programmatic Context Calling** (`ctx.get`)
- **Tool Use Examples** → **Context Use Examples** (session.md)

**Clave**: El agente **llama explícitamente** a `ctx.get --ids X`, no "el sistema inyecta contexto automáticamente".

---

## 🚨 Desalineaciones Reales (Revisadas)

### 1. **Redacción confusa en "Context Pack" (L206-244)**

**Ubicación**: `README.md:206-244`

**Problema de redacción**:

```markdown
El **Context Pack** es un JSON estructurado que permite a los LLMs ingerir
documentación de manera eficiente sin cargar textos completos en el prompt.
```

**Por qué es confuso**:

- Usa lenguaje RAG: "ingerir", "sin cargar textos completos"
- Sugiere que el sistema "entrega" contexto automáticamente
- No refleja que el agente **llama explícitamente** a `ctx.get`

**Corrección propuesta** (alineada con Anthropic):

```markdown
### Context Pack: Índice de Chunks Invocables

El Context Pack es un **índice estructurado** que permite al agente:
1. Descubrir qué chunks existen (`ctx.search`)
2. Invocar chunks específicos (`ctx.get --ids X`)
3. Operar con presupuesto estricto (budget-aware)

**Analogía**: Como "Tool Search Tool" de Anthropic, pero para contexto.

El agente decide qué cargar, cuándo y con qué presupuesto.  
NO es recuperación automática.
```

---

### 2. **Script legacy `ingest_trifecta.py` (L210-218)**

**Ubicación**: `README.md:210-218`

**Problema**:

```bash
# Generar context_pack.json en _ctx/
python scripts/ingest_trifecta.py --segment debug_terminal
```

**Por qué es un problema**:

- Recomienda script legacy cuando existe `trifecta ctx build` (CLI oficial)
- Contradice "usar IDEAS no PRODUCTOS" (filosofía del proyecto)
- Riesgo de divergencia entre script y CLI

**Corrección propuesta**:

```markdown
### Generar Context Pack

```bash
# Comando oficial (recomendado)
trifecta ctx build --segment /path/to/segment

# Validar integridad
trifecta ctx validate --segment /path/to/segment
```

> **DEPRECADO**: `scripts/ingest_trifecta.py` será removido en v2.  
> Usar solo para debugging interno del CLI.

```

---

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

## 📊 Features Avanzados (NO son desalineaciones)

Estos conceptos están **correctos** pero son **Fase 3** (futuro):

### A. **Progressive Disclosure con Scores (L157-163)**

**Status**: ✅ Correcto, pero Fase 3

- Es un feature avanzado, como LSP y AST
- El objetivo es llegar ahí cuando el MVP esté funcional
- No es una contradicción, es una **meta futura**

**Acción**: Agregar nota de fase:

```markdown
## Progressive Disclosure (Fase 3 — Futuro)

> **NOTA**: Feature avanzado. Implementar solo después de validar MVP.

| Nivel | Trigger | Tokens |
|-------|---------|--------|
| **L0** | Score < 0.6 | ~50 (solo frontmatter) |
...
```

### B. **AST/LSP Integration (mencionado en Anthropic)**

**Status**: ✅ Correcto, pero Fase 3

Del artículo de Anthropic (L374-413):
> "When you're working with 5 files that change constantly, markdown headings aren't enough.  
> This is where Tree-sitter and LSP come in."

**Acción**: Ya está correctamente categorizado como Fase 3 en el Roadmap.

---

## 📋 Resumen de Acciones

| Ítem | Acción | Prioridad |
|------|--------|-----------|
| Context Pack redacción | Reescribir con lenguaje PCC (no RAG) | 🔴 ALTA |
| Script legacy | Deprecar `ingest_trifecta.py` | 🔴 ALTA |
| Mini-RAG sección | Aclarar que es herramienta externa | 🟡 MEDIA |
| Progressive Disclosure | Agregar nota "Fase 3" | 🟢 BAJA |
| AST/LSP | Ya está correcto (Roadmap Pending) | ✅ OK |

---

## ✅ Principio Rector (del artículo de Anthropic)

**"Advanced Context Use is a mindset shift: from documents to invokable capabilities."**

- El agente **llama** a `ctx.search` y `ctx.get`
- El sistema **NO inyecta** contexto automáticamente
- El presupuesto es **estricto** (budget-aware)
- La evidencia es **citada** con `[chunk_id]`

**Trifecta = Programming Context Calling, NO RAG.**

---

## 📖 Referencias

- **González, F.** (2025). "Advanced Context Use: Context as Invokable Tools" (artículo original del usuario)
  - Aplica el patrón de Anthropic's "Advanced Tool Use" al dominio de contexto
  - Introduce la analogía: Tool Search → Context Search, Programmatic Tool Calling → Programmatic Context Calling
- **Anthropic** (2024). "Advanced Tool Use in Claude AI". <https://www.anthropic.com/engineering/advanced-tool-use>
  - Artículo original que inspira el patrón aplicado en Trifecta
- **Liu et al.** (2023). "Lost in the Middle: How Language Models Use Long Contexts"
