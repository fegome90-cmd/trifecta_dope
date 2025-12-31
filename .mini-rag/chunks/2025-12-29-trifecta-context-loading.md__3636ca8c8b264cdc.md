## Implementación Mínima Aprobada

**Complejidad contenida**:
1. `digest + index` siempre en prompt (L0)
2. `ctx.search` + `ctx.get(mode, budget)` (L1-L2)
3. Router heurístico simple
4. Presupuesto duro (`max_ctx_rounds=2`, `max_tokens=1200`)
5. Guardrail: "contexto = evidencia"

**Ganancia real**:
- Control de tokens
- Menos ruido
- Progressive disclosure sin LLM extra

**Resultado**: Programmatic Context Calling sobrio. 🚀

---
