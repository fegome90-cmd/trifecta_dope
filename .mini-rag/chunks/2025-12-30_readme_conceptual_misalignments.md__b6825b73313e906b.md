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
