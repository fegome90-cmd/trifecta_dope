#### 3.3.4 Rollback Plan

- Si LSP hangs: Timeout hard-coded 2s, luego disable AST capture automáticamente.
- Si AST events explotan bundle size: Aplicar limit (2MB max por bundle), truncar resto.
- Si pyright no disponible: Feature flag auto-disabled, continuar sin AST.

---
