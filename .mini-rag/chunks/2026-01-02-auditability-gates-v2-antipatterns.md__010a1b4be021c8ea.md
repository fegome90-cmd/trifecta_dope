| Tema | Por qué NO en este sprint | Decisión diferida a | AP Relacionado |
|------|--------------------------|---------------------|---------------|
| **LSP value prop** | LSP es enhancement; AST debe funcionar primero sin daemon | Phase 3b (post-gates) | AP10: Fallback debe estar auditado primero |
| **Tree-sitter completo** | Mock actual satisface contrato mínimo; real parsing es optimización | Phase 4 (performance) | AP2: Tests no deben depender de tool externo |
| **Sistema de locks nuevo** | Ya existe `.autopilot.lock` en use_cases.py; reusar | Reuse, no crear | AP8: SSOT de locks ya existe |
| **Index embeddings** | Trifecta NO es RAG; búsqueda lexical es suficiente | Nunca (por diseño) | — |
| **Refactor arquitectónico** | Cambio de capas sin evidencia es riesgo | Post-gates con data | — |
| **SymbolInfo completo** | No usado en paths críticos; stub suficiente | Cuando se necesite | AP9: No crear compat shims |
| **Scripts legacy removal** | No bloquean gates; limpieza es separada | Sprint de mantenimiento | — |
| **Tests coverage increase** | Objetivo es collecting, no coverage 100% | Sprint de calidad | AP2: Tests deben ser deterministas primero |
| **Daemon lifecycle changes** | TTL 180s funciona; no tocar sin data | Post-gates con telemetry | AP4: Tripwire para shutdown ruidoso |
| **Context pack schema v2** | Schema v1 es funcional; cambio es breaking change | Con
