### 2. AST/LSP (El Motor F1 en el Taller)
- **Propósito**: Navegación de precisión quirúrgica (Go-to-definition, Call graphs).
- **Flujo**: Activación explícita vía CLI (`trifecta ast symbols`).
- **Archivos**: `repo_map.md`, `symbols_stub.md` con `PROMPT_FIX_HINT` para recuperación de errores.
- **Por qué es externo**: Porque es infraestructura pesada que el agente solo debe invocar cuando el Meta-Contexto le ha confirmado *dónde* está el problema.

---
