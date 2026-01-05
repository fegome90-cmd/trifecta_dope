### 4. LSP Control
- **Evidencia**: No hay flag `LSP_OFF` global. El control es reactivo: si `client.is_ready()` es falso, se emite `lsp.fallback`.
- **Simulación**: Matar el daemon (`rm /tmp/hemdov_debug.sock`) fuerza el fallback a AST automático en el siguiente comando `ast symbols`.

---
