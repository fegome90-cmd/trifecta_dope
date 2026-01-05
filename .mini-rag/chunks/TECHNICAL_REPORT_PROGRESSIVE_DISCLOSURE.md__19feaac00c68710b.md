### 6.1 Gaps Identificados

| Gap | Severidad | Ubicación | Impacto |
|-----|-----------|-----------|---------|
| **Score-based Auto PD** | Alta | `ContextService.get` | El agente debe elegir modo manualmente |
| **LSP value prop** | Media | `cli_ast.py` | LSP se usa pero output es siempre AST skeleton |
| **AST Parser stub** | Media | `ast_parser.py` | tree-sitter fue removido por "risk management" |
| **L2 no existe** | Alta | Arquitectura | No hay capa de análisis profundo |
| **Cross-file skeleton** | Baja | `context_pack.json` | No hay skeleton pre-calculado en index |
