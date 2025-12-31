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
